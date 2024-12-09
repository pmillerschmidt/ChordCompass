import * as Tone from 'tone';

class AudioService {
  constructor() {
    // high-pass filter
    this.filter = new Tone.Filter({
      type: "lowpass",
      frequency: 200,
      rolloff: -12
    }).toDestination();
    // chorus
    this.chorus = new Tone.Chorus({
      frequency: 0.5,
      delayTime: 3.5,
      depth: 0.3,
      wet: 0.2
    }).connect(this.filter);
    // sine wave
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
    // square wave
    this.squareSynth = new Tone.PolySynth(Tone.Synth, {
      oscillator: {
        type: "square",
        detune: -5
      },
      envelope: {
        attack: 0.1,
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

  findClosestNotes(prevNotes, nextNotes) {
    if (!prevNotes) return nextNotes;

    // voice lead
    let bestNotes = [...nextNotes];
    let minDistance = Infinity;

    for (let i = -1; i <= 1; i++) {
      for (let j = -1; j <= 1; j++) {
        for (let k = -1; k <= 1; k++) {
          const octaveShifts = [i * 12, j * 12, k * 12];
          const candidateNotes = nextNotes.map((note, idx) => note + octaveShifts[idx]);
          const totalDistance = prevNotes.reduce((sum, prevNote, idx) => {
            return sum + Math.abs(prevNote - candidateNotes[idx]);
          }, 0);
          if (totalDistance < minDistance) {
            minDistance = totalDistance;
            bestNotes = candidateNotes;
          }
        }
      }
    }
    return bestNotes;
  }

  async playChord(notes, duration) {
    const midiToNote = (midi) => {
      const noteNames = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
      const octave = Math.floor((midi) / 12) - 2;
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
    this.stop();
    this._isPlaying = true;
    await Tone.start();
    const secondsPerBeat = 60 / tempo;
    let previousNotes = null;
    for (const chord of chordData) {
      if (!this._isPlaying) break;
      // voice lead
      const optimizedNotes = this.findClosestNotes(previousNotes, chord.notes);
      previousNotes = optimizedNotes;
      const duration = chord.duration * secondsPerBeat / 2;
      await this.playChord(optimizedNotes, duration);
      this._currentTimeout = await new Promise(resolve => setTimeout(resolve, duration * 1000));
    }
    this._currentTimeout = null;
  }

  stop() {
    // clear timeouts
    if (this._currentTimeout) {
      clearTimeout(this._currentTimeout);
      this._currentTimeout = null;
    }
    this._isPlaying = false;
    // stop and clear both synths
    this.sineSynth.releaseAll();
    this.squareSynth.releaseAll();
  }
}

export const audioService = new AudioService();