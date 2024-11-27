from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from generate import generate_progression
from player import ChordPlayer

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize player globally
player = ChordPlayer()

class GenerationRequest(BaseModel):
    seed: str
    length: int = 8

class PlayRequest(BaseModel):
    progression: List[str]
    tempo: int = 120

@app.post("/generate")
async def generate(request: GenerationRequest):
    try:
        progression = generate_progression(request.seed, length=request.length)
        return {"progression": progression}
    except Exception as e:
        print(f"Error generating progression: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/play")
async def play(request: PlayRequest):
    try:
        print(f"Playing progression: {request.progression} at tempo {request.tempo}")
        player.play_progression(request.progression, request.tempo)
        return {"status": "success"}
    except Exception as e:
        print(f"Error playing progression: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    if player:
        player.cleanup()