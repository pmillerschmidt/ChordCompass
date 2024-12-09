from urllib.request import Request

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Tuple, Optional
from pathlib import Path
import torch
import logging
from ChordLSTM import ChordLSTM
from player import ChordPlayer

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://pmillerschmidt.github.io",
        "https://pmillerschmidt.github.io/ChordCompass",
        "https://chordcompass-1.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# model setup
device = torch.device("cpu")  # Use CPU for serving
MODEL_PATH = "checkpoints/final_model.pt"

class PlayRequest(BaseModel):
    progression: List[dict]  # Will contain chord and duration
    tempo: int = 120
    tonic: str = "C"
    mode: str = "M"

player = None

@app.on_event("startup")
async def startup_event():
    global player
    player = ChordPlayer()
    print("ChordPlayer initialized")

@app.on_event("shutdown")
async def shutdown_event():
    global player
    if player:
        player.cleanup()
        print("ChordPlayer cleaned up")


def load_model(checkpoint_path: Path) -> Tuple[ChordLSTM, dict]:
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    chord_to_idx = checkpoint['vocab']
    model = ChordLSTM(
        vocab_size=len(chord_to_idx),
        hidden_dim=64
    ).to(device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    return model, chord_to_idx


# load model
try:
    model, chord_to_idx = load_model(Path(MODEL_PATH))
    idx_to_chord = {idx: chord for chord, idx in chord_to_idx.items()}
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Error loading model: {e}")
    raise


class GenerationRequest(BaseModel):
    length: int = 8
    temperature: float = 1.0
    start_chord: str = 'I'


class ProgressionResponse(BaseModel):
    chords: List[str]
    durations: List[int]
    total_bars: float

def generate_progression(
    length: int,
    temperature: float = 1.0,
    start_chord: str = None
) -> Tuple[List[str], List[int]]:
    sequence_length = 2  # same as training
    # default to roo
    start = start_chord if start_chord else 'I'
    seed_progression = [start] * sequence_length
    seed_indices = [chord_to_idx.get(chord, 0) for chord in seed_progression]
    current_sequence = torch.LongTensor([seed_indices]).to(device)
    chords = []
    durations = []
    with torch.no_grad():
        for _ in range(length):
            chord_logits, duration_logits = model(current_sequence)
            # temp
            chord_logits = chord_logits / temperature
            duration_logits = duration_logits / temperature
            # next chord
            chord_probs = torch.softmax(chord_logits, dim=1)
            next_chord_idx = torch.multinomial(chord_probs[0], 1).item()
            next_chord = idx_to_chord[next_chord_idx]
            # next dur
            duration_probs = torch.softmax(duration_logits, dim=1)
            duration_idx = torch.multinomial(duration_probs[0], 1).item()
            next_duration = duration_idx + 1
            chords.append(next_chord)
            durations.append(next_duration)
            # update
            current_sequence = torch.cat([
                current_sequence[:, 1:],
                torch.LongTensor([[next_chord_idx]]).to(device)
            ], dim=1)
    return chords, durations


@app.get("/available_chords")
async def get_available_chords():
    """Return the list of available chord symbols"""
    return {"chords": list(chord_to_idx.keys())}


@app.post("/generate", response_model=ProgressionResponse)
async def generate(request: GenerationRequest):
    try:
        logger.info(f"Generating progression: length={request.length}, "
                    f"temp={request.temperature}, start={request.start_chord}")
        if request.start_chord not in chord_to_idx:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid start chord. Available chords: {list(chord_to_idx.keys())}"
            )
        chords, durations = generate_progression(
            length=request.length,
            temperature=request.temperature,
            start_chord=request.start_chord
        )
        total_bars = sum(d / 8.0 for d in durations)
        return ProgressionResponse(
            chords=chords,
            durations=durations,
            total_bars=total_bars
        )
    except Exception as e:
        logger.error(f"Error generating progression: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "model_loaded": model is not None}


@app.post("/play")
async def play(request: PlayRequest):
    try:
        logger.info(f"Generating notes for progression: {request.progression}")

        # Return the chord information with actual notes to play
        chord_data = []
        for chord in request.progression:
            notes = player.roman_to_midi_notes(chord['chord'], request.tonic, request.mode)
            chord_data.append({
                'chord': chord['chord'],
                'duration': chord['duration'],
                'notes': notes  # MIDI note numbers
            })

        return {"chord_data": chord_data}

    except Exception as e:
        logger.error(f"Error processing progression: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/drum_patterns")
async def get_drum_patterns():
    """Return the list of available drum patterns"""
    return {
        "patterns": [
            {"value": key, "label": key.title() + " Beat"}
            for key in DRUM_PATTERNS.keys()
        ]
    }
@app.post("/stop")
async def stop():
    try:
        player.stop_playback()
        return {"status": "success"}
    except Exception as e:
        print(f"Error stopping playback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"[DEBUG] Received {request.method} request to {request.url}")
    print(f"[DEBUG] Headers: {request.headers}")
    response = await call_next(request)
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

