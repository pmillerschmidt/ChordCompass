from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Tuple
from pathlib import Path
import torch
import logging
from ChordLSTM import ChordLSTM
from player import ChordPlayer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model setup
device = torch.device("cpu")  # Use CPU for serving
MODEL_PATH = "checkpoints/final_model.pt"  # Update with your model path

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


# Load model at startup
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
    """Generate a chord progression"""
    sequence_length = 2  # Should match training
    # Use 'I' as default if no start_chord provided
    start = start_chord if start_chord else 'I'
    seed_progression = [start] * sequence_length
    # Convert seed progression to indices
    seed_indices = [chord_to_idx.get(chord, 0) for chord in seed_progression]
    current_sequence = torch.LongTensor([seed_indices]).to(device)
    chords = []
    durations = []
    with torch.no_grad():
        for _ in range(length):
            chord_logits, duration_logits = model(current_sequence)
            # Apply temperature scaling
            chord_logits = chord_logits / temperature
            duration_logits = duration_logits / temperature
            # Sample next chord
            chord_probs = torch.softmax(chord_logits, dim=1)
            next_chord_idx = torch.multinomial(chord_probs[0], 1).item()
            next_chord = idx_to_chord[next_chord_idx]
            # Sample duration (1-8 eighth notes)
            duration_probs = torch.softmax(duration_logits, dim=1)
            duration_idx = torch.multinomial(duration_probs[0], 1).item()
            next_duration = duration_idx + 1  # Convert back to 1-8 range
            chords.append(next_chord)
            durations.append(next_duration)
            # Update sequence
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

class PlayRequest(BaseModel):
    progression: List[dict]  # Will contain chord and duration
    tempo: int = 120
    tonic: str = "C"
    mode: str = "M"
@app.post("/play")
async def play(request: PlayRequest):
    try:
        print(f"Playing progression: {request.progression} in {request.tonic} {request.mode} at {request.tempo} BPM")
        player.play_progression(
            request.progression,
            tempo=request.tempo,
            tonic=request.tonic,
            mode=request.mode
        )
        return {"status": "success"}
    except Exception as e:
        print(f"Error playing progression: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop")
async def stop():
    try:
        player.stop_playback()
        return {"status": "success"}
    except Exception as e:
        print(f"Error stopping playback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)