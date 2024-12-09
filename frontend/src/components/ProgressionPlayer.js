import React, { useState, useRef } from 'react';
import { Button } from './ui/button';
import { Slider } from './ui/slider';
import { Card, CardContent } from './ui/card';
import { Play, Pause, Music2 } from 'lucide-react';
import { Alert, AlertDescription } from "./ui/alert";
import { audioService } from '../services/audioService';

const API_URL = 'https://chordcompass-1.onrender.com';
// const API_URL = 'http://0.0.0.0:8000';

const NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];


export default function ProgressionPlayer({ progression }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [tempo, setTempo] = useState(120);
  const [tonic, setTonic] = useState('C');
  const [error, setError] = useState(null);

  const stopPlayback = async () => {
    try {
      console.log("[DEBUG] Stopping playback");
      audioService.stop();
      setIsPlaying(false);
    } catch (error) {
      console.error('Error stopping playback:', error);
    }
};

const playProgression = async () => {
    try {
      setIsPlaying(true);
      setError(null);

      const response = await fetch(`${API_URL}/play`, {
        method: 'POST',
        mode: 'cors',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          progression,
          tempo,
          tonic,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get chord data');
      }

      const { chord_data } = await response.json();
      await audioService.playProgression(chord_data, tempo);

    } catch (error) {
      console.error('Error playing progression:', error);
      setError(error.message || 'Failed to play progression');
    } finally {
      setIsPlaying(false);
    }
};

const togglePlay = async () => {
    console.log("[DEBUG] Toggle play clicked. Current state:", { isPlaying });

    if (isPlaying) {
        await stopPlayback();
    } else {
        playProgression();
    }
};

  return (
    <Card className="w-full mt-4">
      <CardContent className="pt-6">
        <div className="grid gap-6">
          {/* Key Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Key (Major)</label>
            <div className="flex flex-wrap gap-2">
              {NOTES.map(note => (
                <Button
                  key={note}
                  variant="outline"
                  className={`px-3 py-1 ${note === tonic ? 'bg-blue-500 text-white hover:bg-blue-600' : ''}`}
                  onClick={() => setTonic(note)}
                  disabled={isPlaying}
                >
                  {note}
                </Button>
              ))}
            </div>
          </div>

          {/* Tempo and Play Controls */}
          <div className="flex items-center space-x-4">
            <Button
              onClick={() => {
                console.log('Button clicked!');
                togglePlay();
              }}
              variant="outline"
              size="icon"
              className="h-10 w-10"
            >
              {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            </Button>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Tempo: {tempo} BPM</span>
                <Music2 className="h-4 w-4 text-muted-foreground" />
              </div>
              <Slider
                value={[tempo]}
                onValueChange={([value]) => setTempo(value)}
                min={60}
                max={200}
                step={1}
                className="w-full"
                disabled={isPlaying}
              />
            </div>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="flex flex-wrap gap-2">
            {progression.map((chord, index) => (
              <div
                key={index}
                className={`p-2 rounded ${
                  isPlaying ? 'bg-primary text-primary-foreground' : 'bg-secondary'
                }`}
              >
                {chord.chord} ({chord.duration})
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}