import React, { useState, useRef } from 'react';
import { Button } from './ui/button';
import { Slider } from './ui/slider';
import { Card, CardContent } from './ui/card';
import { Play, Pause, Music2, Drum } from 'lucide-react';
import { Alert, AlertDescription } from "./ui/alert";
import { Switch } from './ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";

const API_URL = 'https://chordcompass-1.onrender.com';

const NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const DRUM_PATTERNS = [
  { value: 'basic', label: 'Basic Beat' },
  { value: 'rock', label: 'Rock Beat' },
  { value: 'jazz', label: 'Jazz Ride' },
];

export default function ProgressionPlayer({ progression }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [tempo, setTempo] = useState(120);
  const [tonic, setTonic] = useState('C');
  const [error, setError] = useState(null);
  const [drumsEnabled, setDrumsEnabled] = useState(false);
  const [drumPattern, setDrumPattern] = useState('basic');
  const abortControllerRef = useRef(null);

  const stopPlayback = async () => {
    try {
      await fetch(`${API_URL}/stop`, {
        method: 'POST',
        mode: 'cors',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });
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
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          progression,
          tempo,
          tonic,
          drums: {
            enabled: drumsEnabled,
            pattern: drumPattern
          }
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Server error');
      }

      const totalBeats = progression.reduce((sum, { duration }) => sum + duration, 0);
      const durationInSeconds = (totalBeats * 60) / (tempo * 2);
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
      await stopPlayback();
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

          {/* Drum Controls */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Drum className="h-4 w-4 text-muted-foreground" />
                <label className="text-sm font-medium">Enable Drums</label>
              </div>
              <Switch
                checked={drumsEnabled}
                onCheckedChange={setDrumsEnabled}
                disabled={isPlaying}
              />
            </div>

            {drumsEnabled && (
              <Select
                value={drumPattern}
                onValueChange={setDrumPattern}
                disabled={isPlaying}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select drum pattern" />
                </SelectTrigger>
                <SelectContent>
                  {DRUM_PATTERNS.map(pattern => (
                    <SelectItem key={pattern.value} value={pattern.value}>
                      {pattern.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
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