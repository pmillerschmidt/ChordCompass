import React, { useState } from 'react';
import ChordGenerator from './components/ChordGenerator';
import ProgressionPlayer from './components/ProgressionPlayer';

export default function App() {
  const [currentProgression, setCurrentProgression] = useState(null);

  const handleProgressionGenerated = (progression) => {
    setCurrentProgression(progression);
  };

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-background">
      <div className="container mx-auto px-4 py-8">
        <div className="mx-auto max-w-2xl">
          <header className="mb-12 text-center">
            <h1 className="mb-4 text-4xl font-bold text-primary">ChordCompass</h1>
            <p className="text-lg text-muted-foreground">
              Generate and play chord progressions
            </p>
          </header>

          <div className="space-y-8">
            <ChordGenerator onProgressionGenerated={handleProgressionGenerated} />

            {currentProgression && (
              <ProgressionPlayer progression={currentProgression} />
            )}
          </div>

          <footer className="mt-12 text-center text-sm text-muted-foreground">
            <p>Created with FastAPI and React</p>
          </footer>
        </div>
      </div>
    </div>
  );
}