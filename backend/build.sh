#!/bin/bash

# Install system dependencies
apt-get update && apt-get install -y \
    fluidsynth \
    pulseaudio \
    alsa-utils \
    libasound2-dev \
    libportaudio2

# Configure PulseAudio
mkdir -p /var/run/pulse
pulseaudio --system --daemonize --verbose

# Configure ALSA
echo "
pcm.!default {
    type pulse
    fallback \"sysdefault\"
}
ctl.!default {
    type pulse
    fallback \"sysdefault\"
}
" > /etc/asound.conf