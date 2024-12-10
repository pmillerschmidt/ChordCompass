import React, { useState } from 'react';
import { Button } from './ui/button';
import { Slider } from './ui/slider';
import { Card, CardContent } from './ui/card';
import { Play, Pause, Music2 } from 'lucide-react';
import { Alert, AlertDescription } from "./ui/alert";
import { audioService } from '../services/audioService';

const NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];

export default function ProgressionPlayer({ progression }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [tempo, setTempo] = useState(120);
  const [key, setKey] = useState('C');  // Default key of C
  const [error, setError] = useState(null);

  const stopPlayback = () => {
    console.log("[DEBUG] Stopping playback");
    audioService.stop();
    setIsPlaying(false);
  };

  const playProgression = async () => {
    try {
      setIsPlaying(true);
      setError(null);

      const keyOffset = NOTES.indexOf(key);
      const transposedProgression = {
        ...progression,
        chords: progression.chords.map(chordData => ({
          ...chordData,
          chord: {
            ...chordData.chord,
            notes: chordData.chord.notes.map(note => note + keyOffset)
          }
        }))
      };

      await audioService.playProgression(transposedProgression.chords, tempo);
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
      stopPlayback();
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
                  className={`px-3 py-1 ${note === key ? 'bg-blue-500 text-white hover:bg-blue-600' : ''}`}
                  onClick={() => setKey(note)}
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

          {/* Display Progression */}
          <div className="flex flex-wrap gap-2">
            {progression.chords.map((chordData, index) => (
              <div
                key={index}
                className={`p-2 rounded ${
                  isPlaying ? 'bg-primary text-primary-foreground' : 'bg-secondary'
                }`}
              >
                {chordData.chord.chord}
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}