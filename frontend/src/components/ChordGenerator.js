import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { generateProgression } from '../services/api';
import { Alert, AlertDescription } from "./ui/alert";
import { Loader2 } from "lucide-react";

export default function ChordGenerator({ onProgressionGenerated }) {
  const [length, setLength] = useState(4);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await generateProgression(length);
      onProgressionGenerated(data.chords.map((chord, i) => ({
        chord,
        duration: data.durations[i]
      })));
    } catch (error) {
      setError('Failed to generate progression. Please try again.');
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader className="text-center">
        <CardTitle>Generate a Progression</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex flex-col items-center gap-4">
          <label className="text-sm font-medium">Length</label>
          <div className="flex gap-4">
            <Button
              variant="outline"
              onClick={() => setLength(4)}
              className={`w-24 ${length === 4 ? 'bg-blue-500 text-white hover:bg-blue-600' : ''}`}
              disabled={loading}
            >
              4 Bars
            </Button>
            <Button
              variant="outline"
              onClick={() => setLength(8)}
              className={`w-24 ${length === 8 ? 'bg-blue-500 text-white hover:bg-blue-600' : ''}`}
              disabled={loading}
            >
              8 Bars
            </Button>
          </div>
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
              'Generate'
            )}
          </Button>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}