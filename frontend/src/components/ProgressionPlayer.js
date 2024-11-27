import React, { useState } from 'react';
import { Button } from './ui/button';
import { Slider } from './ui/slider';
import { Card, CardContent } from './ui/card';
import { Play, Pause, Music2 } from 'lucide-react';
import { Alert, AlertDescription } from "./ui/alert";

export default function ProgressionPlayer({ progression }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [tempo, setTempo] = useState(120);
  const [error, setError] = useState(null);

  const playProgression = async () => {
    try {
      setIsPlaying(true);
      setError(null);

      console.log("Sending progression to server:", progression);

      const response = await fetch('http://localhost:8000/play', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          progression,
          tempo,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Server error');
      }

      const data = await response.json();
      console.log("Server response:", data);

      // Wait for the progression to finish playing
      const durationInSeconds = (progression.length * 60) / tempo;
      await new Promise(resolve => setTimeout(resolve, durationInSeconds * 1000));

    } catch (error) {
      console.error('Error playing progression:', error);
      setError(error.message || 'Failed to play progression');
    } finally {
      setIsPlaying(false);
    }
  };

  const togglePlay = () => {
    if (!isPlaying) {
      playProgression();
    }
  };

  return (
    <Card className="w-full mt-4">
      <CardContent className="pt-6">
        <div className="flex items-center space-x-4 mb-4">
          <Button
            onClick={togglePlay}
            variant="outline"
            size="icon"
            className="h-10 w-10"
            disabled={isPlaying}
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
          <Alert variant="destructive" className="mb-4">
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
              {chord}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}