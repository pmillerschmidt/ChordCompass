import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Slider } from './ui/slider';
import { generateProgression } from '../services/api';
import { Alert, AlertDescription } from "./ui/alert";
import { Loader2 } from "lucide-react";

export default function ChordGenerator({ onProgressionGenerated }) {
  const [seed, setSeed] = useState('I-V-vi');
  const [length, setLength] = useState(8);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);

    try {
      const { progression } = await generateProgression(seed, length);
      onProgressionGenerated(progression);
    } catch (error) {
      setError('Failed to generate progression. Please try again.');
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader className="text-center">
        <CardTitle>Chord Progression Generator</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <label className="block text-sm font-medium text-center">Seed Progression</label>
          <Input
            value={seed}
            onChange={(e) => setSeed(e.target.value)}
            placeholder="Enter seed (e.g., I-V-vi)"
            className="max-w-md mx-auto"
            disabled={loading}
          />
        </div>

        <div className="space-y-2 max-w-md mx-auto">
          <label className="block text-sm font-medium text-center">Length: {length}</label>
          <Slider
            value={[length]}
            onValueChange={([value]) => setLength(value)}
            min={4}
            max={16}
            step={1}
            disabled={loading}
          />
        </div>

        <div className="flex justify-center">
          <Button
            onClick={handleGenerate}
            disabled={loading}
            className="min-w-[200px]"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              'Generate Progression'
            )}
          </Button>
        </div>

        {error && (
          <Alert variant="destructive" className="mt-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}