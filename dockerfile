FROM python:3.11

# Install system dependencies
RUN apt-get update && apt-get install -y \
    fluidsynth \
    pulseaudio \
    alsa-utils \
    libasound2-dev

WORKDIR /app

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

# Copy backend code and soundfonts
COPY backend/ .

# Start pulseaudio daemon and run the app
CMD pulseaudio -D && \
    PYTHONPATH=$PYTHONPATH:/app gunicorn main:app \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:10000