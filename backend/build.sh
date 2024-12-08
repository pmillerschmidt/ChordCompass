#!/bin/bash

# Install dependencies
apt-get update && apt-get install -y \
    fluidsynth \
    pulseaudio \
    alsa-utils \
    libasound2

# Configure PulseAudio
mkdir -p /tmp/pulse
pulseaudio --system --daemonize --verbose \
    --exit-idle-time=-1 \
    --system \
    --disallow-exit \
    -L 'module-native-protocol-unix auth-anonymous=1 socket=/tmp/pulseaudio.socket'

# Start your application
cd backend && RENDER=true PYTHONPATH=$PYTHONPATH:/opt/render/project/src/backend gunicorn main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:10000