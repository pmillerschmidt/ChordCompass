// src/services/audioService.js
import * as Tone from 'tone';

class AudioService {
  constructor() {
    // Create a high-pass filter
    this.filter = new Tone.Filter({
      type: "lowpass",
      frequency: 200,
      rolloff: -12
    }).toDestination();

    // Add subtle chorus to help with phase issues
    this.chorus = new Tone.Chorus({
      frequency: 0.5,
      delayTime: 3.5,
      depth: 0.3,
      wet: 0.2
    }).connect(this.filter);

    // Create sine wave synth
    this.sineSynth = new Tone.PolySynth(Tone.Synth, {
      oscillator: {
        type: "sine",
        detune: 0  // Keep sine at base frequency
      },
      envelope: {
        attack: 0.1,
        decay: 0.3,
        sustain: 0.2,
        release: 0.6
      },
      portamento: 0.05,
      volume: -12
    }).connect(this.chorus);

    // Create square wave synth
    this.squareSynth = new Tone.PolySynth(Tone.Synth, {
      oscillator: {
        type: "square",
        detune: -5  // Slightly detune square wave
      },
      envelope: {
        attack: 0.1,  // Slightly different envelope
        decay: 0.28,
        sustain: 0.2,
        release: 0.6
      },
      portamento: 0.05,
      volume: -16
    }).connect(this.chorus);
    this._currentTimeout = null;
    this._isPlaying = false;
  }

  async playChord(notes, duration) {
    const midiToNote = (midi) => {
      const noteNames = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
      // Transpose down 2 octaves from current
      const octave = Math.floor((midi) / 12) - 2;  // Changed from -1 to -3
      const noteName = noteNames[midi % 12];
      return `${noteName}${octave}`;
    };

    const noteNames = notes.map(midiToNote);
    console.log("[DEBUG] Playing notes:", noteNames);
    await Tone.start();
    this.sineSynth.triggerAttackRelease(noteNames, duration);
    this.squareSynth.triggerAttackRelease(noteNames, duration);
}


  async playProgression(chordData, tempo) {
    // Clear any existing playback first
    this.stop();

    this._isPlaying = true;
    await Tone.start();
    const secondsPerBeat = 60 / tempo;

    for (const chord of chordData) {
      if (!this._isPlaying) break;  // Check if we should stop

      const duration = chord.duration * secondsPerBeat / 2;
      await this.playChord(chord.notes, duration);
      // Store timeout reference
      this._currentTimeout = await new Promise(resolve => setTimeout(resolve, duration * 1000));
    }

    // Clear timeout reference after playback completes
    this._currentTimeout = null;
  }

  stop() {
    // Clear any scheduled timeouts
    if (this._currentTimeout) {
      clearTimeout(this._currentTimeout);
      this._currentTimeout = null;
    }

    this._isPlaying = false;

    // Stop and clear both synths
    this.sineSynth.releaseAll();
    this.squareSynth.releaseAll();
  }
}

export const audioService = new AudioService();