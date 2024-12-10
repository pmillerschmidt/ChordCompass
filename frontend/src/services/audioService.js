import * as Tone from 'tone';


// Add interval constants at the top of AudioService.js
const INTERVALS = {
  'C': 60,
  'C#': 61,
  'D': 62,
  'D#': 63,
  'E': 64,
  'F': 65,
  'F#': 66,
  'G': 67,
  'G#': 68,
  'A': 69,
  'A#': 70,
  'B': 71
};

const SCALE_DEGREES = {
  'I': 0,
  'ii': 2,
  'iii': 4,
  'IV': 5,
  'V': 7,
  'vi': 9,
  'vii°': 11
};

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

    // Kick
    this.kick = new Tone.MembraneSynth({
      pitchDecay: 0.05,
      octaves: 6,
      oscillator: { type: "sine" },
      envelope: {
        attack: 0.001,
        decay: 0.4,
        sustain: 0.01,
        release: 0.4
      }
    }).toDestination();
    this.kick.volume.value = -6;

    // Snare
    this.snare = new Tone.NoiseSynth({
      noise: { type: "pink" },
      envelope: {
        attack: 0.005,
        decay: 0.2,
        sustain: 0,
        release: 0.1
      }
    })
    .connect(new Tone.Filter({
      frequency: 2000,
      type: "bandpass"
    }))
    .connect(new Tone.Filter({
      frequency: 3000,
      type: "lowpass",
      rolloff: -12
    }))
    .toDestination();
    this.snare.volume.value = -15;

    // Hi-hat
    this.hihat = new Tone.NoiseSynth({
      noise: { type: "white" },
      envelope: {
        attack: 0.001,
        decay: 0.05,
        sustain: 0,
        release: 0.05
      }
    })
    .connect(new Tone.Filter({
      frequency: 10000,
      type: "highpass"
    }))
    .connect(new Tone.Filter({
      frequency: 5000,
      type: "lowpass",
      rolloff: -24
    }))
    .toDestination();
    this.hihat.volume.value = -10;

    this._currentTimeout = null;
    this._isPlaying = false;
    this._pattern = null;
    this._chordQueue = [];  // Add this to track pending chords
  }

  romanToNotes(romanNumeral, key = 'C') {
    const baseNote = INTERVALS[key];
    const interval = SCALE_DEGREES[romanNumeral];
    const root = baseNote + interval;
    const isMinor = romanNumeral === romanNumeral.toLowerCase();

    return [
      root,
      root + (isMinor ? 3 : 4),  // minor third or major third
      root + 7                    // perfect fifth
    ];
  }

  async playChord(chord, duration) {
    const notes = this.romanToNotes(chord, 'C');  // can make key configurable
    const noteNames = notes.map(midi => {
      const noteNames = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
      const octave = Math.floor((midi) / 12) - 2;
      const noteName = noteNames[midi % 12];
      return `${noteName}${octave}`;
    });

    await Tone.start();
    this.sineSynth.triggerAttackRelease(noteNames, duration);
    this.squareSynth.triggerAttackRelease(noteNames, duration);
  }


  startDrumSequence(tempo) {
    this._pattern = new Tone.Sequence((time, step) => {
      if (step === 0) {
        this.kick.triggerAttackRelease('C1', '8n', time);
      } else if (step === 1) {
        this.hihat.triggerAttackRelease('16n', time);
      } else if (step === 2) {
        this.kick.triggerAttackRelease('C1', '8n', time);
        this.snare.triggerAttackRelease('8n', time);
      } else if (step === 3) {
        this.hihat.triggerAttackRelease('16n', time);
      }
    }, [0, 1, 2, 3], '8n');

    Tone.getTransport().bpm.value = tempo;
    this._pattern.start(0);

    if (Tone.getTransport().state !== 'started') {
      Tone.getTransport().start();
    }
  }

  async playProgression(chordData, tempo) {
    // Ensure thorough cleanup
    await this.stop();

    // Reset and set up new progression
    this._chordQueue = [...chordData];  // Store the new progression
    this._isPlaying = true;
    await Tone.start();
    this.startDrumSequence(tempo);

    const secondsPerBeat = 60 / tempo;

    while (this._chordQueue.length > 0 && this._isPlaying) {
      const chord = this._chordQueue[0];
      const duration = chord.duration * secondsPerBeat / 2;
      await this.playChord(chord.notes, duration);
      this._chordQueue.shift();  // Remove the played chord
      if (this._isPlaying) {  // Only set timeout if still playing
        this._currentTimeout = await new Promise(resolve => setTimeout(resolve, duration * 1000));
      }
    }

    this._currentTimeout = null;
    this.stop();
  }

  async stop() {
    // Clear the chord queue
    this._chordQueue = [];

    if (this._currentTimeout) {
      clearTimeout(this._currentTimeout);
      this._currentTimeout = null;
    }

    if (this._pattern) {
      this._pattern.stop();
      Tone.getTransport().stop();
    }

    this._isPlaying = false;

    // Ensure synths are cleared
    this.sineSynth.releaseAll();
    this.squareSynth.releaseAll();

    // Give time for cleanup
    await new Promise(resolve => setTimeout(resolve, 100));
  }
}

export const audioService = new AudioService();