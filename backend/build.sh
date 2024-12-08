#!/bin/bash

# Install dependencies
apt-get update && apt-get install -y \
    fluidsynth \
    pulseaudio \
    alsa-utils \
    libasound2

# Stop any existing PulseAudio processes
killall pulseaudio || true

# Configure PulseAudio
mkdir -p /var/run/pulse
mkdir -p /var/lib/pulse
mkdir -p /tmp/pulse

# Create PulseAudio configuration
cat > /etc/pulse/daemon.conf <<EOF
daemonize = yes
exit-idle-time = -1
allow-module-loading = yes
allow-exit = no
EOF

# Start PulseAudio with specific configuration
pulseaudio --system \
    --disallow-exit \
    --disallow-module-loading=0 \
    --load="module-native-protocol-unix auth-anonymous=1 socket=/tmp/pulseaudio.socket" \
    --exit-idle-time=-1 \
    --daemonize

# Wait for PulseAudio to start
sleep 2

# Verify PulseAudio is running
pactl info || echo "PulseAudio failed to start"

# Start your application
cd backend && RENDER=true PYTHONPATH=$PYTHONPATH:/opt/render/project/src/backend gunicorn main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:10000