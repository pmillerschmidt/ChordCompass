#!/bin/bash

# Update and install dependencies
apt-get update
apt-get install -y fluidsynth pulseaudio alsa-utils libasound2-dev

# Start pulseaudio daemon
pulseaudio -D

# Configure pulseaudio
pacmd load-module module-null-sink sink_name=dummy sink_properties=device.description=dummy_output

# Create audio group and add user if needed
groupadd -f audio
usermod -a -G audio root

# Start alsa
service alsa-utils start

# Load snd-dummy module if needed
modprobe snd-dummy || true

exit 0