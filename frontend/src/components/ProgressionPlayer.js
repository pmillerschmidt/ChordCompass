import React, { useState, useEffect } from 'react';
import { audioService } from '../services/audioService';


export default function ProgressionPlayer({ progression }) {
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    return () => {
      audioService.stop();
      setIsPlaying(false);
    };
  }, [progression]);

  const togglePlay = async () => {
    console.log("[DEBUG] Toggle play clicked. Current state:", { isPlaying });

    if (isPlaying) {
      console.log("[DEBUG] Stopping playback");
      audioService.stop();
      setIsPlaying(false);
    } else if (progression?.chords) {  // Check if chords exist
      console.log("[DEBUG] Starting playback");
      setIsPlaying(true);

      try {
        await audioService.playProgression(progression.chords, progression.tempo);
        setIsPlaying(false);
      } catch (error) {
        console.error("Error playing progression:", error);
        setIsPlaying(false);
      }
    }
  };

  // Early return if no progression or chords
  if (!progression?.chords) {
    return null;
  }

  return (
    <div className="rounded-lg border bg-card p-4 text-card-foreground shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Progression Player</h2>
        <button
          onClick={togglePlay}
          className={`rounded-md px-4 py-2 ${
            isPlaying
              ? 'bg-red-500 text-white hover:bg-red-600'
              : 'bg-primary text-primary-foreground hover:bg-primary/90'
          }`}
        >
          {isPlaying ? 'Stop' : 'Play'}
        </button>
      </div>

      {progression.chords && (
        <div className="mt-4">
          <h3 className="font-medium">Current Progression:</h3>
          <div className="mt-2 flex flex-wrap gap-2">
            {progression.chords.map((chord, index) => (
              <div
                key={index}
                className="rounded bg-muted px-2 py-1 text-sm text-muted-foreground"
              >
                {chord.name}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}