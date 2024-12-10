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
    this._currentProgression = null;
  }

  async playChord(chordData, duration) {
    const midiToNote = (midi) => {
      const noteNames = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
      const octave = Math.floor((midi) / 12) - 2;
      const noteName = noteNames[midi % 12];
      return `${noteName}${octave}`;
    };

    // Access the notes from the nested structure
    const notes = chordData.chord.notes;
    if (!notes) {
      console.error('Invalid chord data:', chordData);
      return;
    }

    const noteNames = notes.map(midiToNote);
    console.log("[DEBUG] Playing notes:", noteNames);
    await Tone.start();
    this.sineSynth.triggerAttackRelease(noteNames, duration);
    this.squareSynth.triggerAttackRelease(noteNames, duration);
  }

    startDrumSequence(tempo) {
      const transport = Tone.getTransport();
      transport.bpm.value = tempo;

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

      if (transport.state !== 'started') {
        transport.start();
      }
      this._pattern.start(0);
    }

  async playProgression(progression, tempo) {
      // Clear any existing playback
      this.stop();
      await new Promise(resolve => setTimeout(resolve, 100));

      this._isPlaying = true;
      this._currentProgression = progression;
      await Tone.start();

      // Clean transport state using getTransport
      const transport = Tone.getTransport();
      transport.cancel();
      this.startDrumSequence(tempo);

      const secondsPerBeat = 60 / tempo;

      for (const chord of progression) {
        if (!this._isPlaying || this._currentProgression !== progression) {
          break;
        }
        const duration = chord.duration * secondsPerBeat / 2;
        await this.playChord(chord, duration);
        this._currentTimeout = await new Promise(resolve => setTimeout(resolve, duration * 1000));
      }

      this._currentTimeout = null;
      this._currentProgression = null;
      this.stop();
    }

  stop() {
    if (this._currentTimeout) {
      clearTimeout(this._currentTimeout);
      this._currentTimeout = null;
    }

    if (this._pattern) {
      this._pattern.stop();
      this._pattern.dispose();
      this._pattern = null;

      const transport = Tone.getTransport();
      transport.stop();
      transport.cancel();
    }

    this._isPlaying = false;
    this._currentProgression = null;

    this.sineSynth.releaseAll();
    this.squareSynth.releaseAll();
  }
}

export const audioService = new AudioService();