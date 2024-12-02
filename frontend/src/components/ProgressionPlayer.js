import React, { useState, useRef } from 'react';
import { Button } from './ui/button';
import { Slider } from './ui/slider';
import { Card, CardContent } from './ui/card';
import { Play, Pause, Music2 } from 'lucide-react';
import { Alert, AlertDescription } from "./ui/alert";

const NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const MODES = [
  { value: 'M', label: 'Major' },
  { value: 'm', label: 'Minor' }
];

export default function ProgressionPlayer({ progression }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [tempo, setTempo] = useState(120);
  const [tonic, setTonic] = useState('C');
  const [mode, setMode] = useState('M');
  const [error, setError] = useState(null);
  const abortControllerRef = useRef(null);

  const stopPlayback = async () => {
    try {
      await fetch('http://localhost:8000/stop', {
        method: 'POST',
      });
    } catch (error) {
      console.error('Error stopping playback:', error);
    }
  };

  const playProgression = async () => {
  try {
    setIsPlaying(true);
    setError(null);

    const response = await fetch('http://localhost:8000/play', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        progression,
        tempo,
        tonic,
        mode
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Server error');
    }

    // Calculate total duration based on actual chord durations
    const totalBeats = progression.reduce((sum, { duration }) => sum + duration, 0);
    const durationInSeconds = (totalBeats * 60) / (tempo * 2);

    // Keep isPlaying true until playback finishes
    await new Promise(resolve => setTimeout(resolve, durationInSeconds * 1000));

  } catch (error) {
    console.error('Error playing progression:', error);
    setError(error.message || 'Failed to play progression');
  } finally {
    setIsPlaying(false);
  }
};

const togglePlay = async () => {
  if (isPlaying) {
    await fetch('http://localhost:8000/stop', {
      method: 'POST',
    });
    setIsPlaying(false);
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
            <label className="text-sm font-medium">Key</label>
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

          {/* Mode Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Mode</label>
            <div className="flex gap-2">
              {MODES.map(({ value, label }) => (
                <Button
                  key={value}
                  variant="outline"
                  className={`px-4 ${value === mode ? 'bg-blue-500 text-white hover:bg-blue-600' : ''}`}
                  onClick={() => setMode(value)}
                  disabled={isPlaying}
                >
                  {label}
                </Button>
              ))}
            </div>
          </div>

          {/* Tempo and Play Controls */}
          <div className="flex items-center space-x-4">
            <Button
            onClick={togglePlay}
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