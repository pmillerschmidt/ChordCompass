import subprocess
import time
import os
import threading
from queue import Queue


class ChordPlayer:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.soundfont_path = os.path.join(current_dir, "soundfonts", "piano.sf2")

        if not os.path.exists(self.soundfont_path):
            raise FileNotFoundError(f"Soundfont not found at {self.soundfont_path}")

        print(f"Using soundfont: {self.soundfont_path}")

        # Simplified FluidSynth settings for just piano playback
        cmd = [
            "fluidsynth",
            "-a", "pulseaudio",  # audio driver
            "-g", "2",  # gain
            "-r", "44100",  # sample rate
            self.soundfont_path
        ]
        print(f"Starting FluidSynth with command: {' '.join(cmd)}")

        try:
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print("FluidSynth initialized successfully")
        except Exception as e:
            print(f"Error starting FluidSynth: {e}")
            raise

        # Note mapping with chromatic notes
        self.notes = {
            'C': 60, 'C#': 61, 'Db': 61,
            'D': 62, 'D#': 63, 'Eb': 63,
            'E': 64,
            'F': 65, 'F#': 66, 'Gb': 66,
            'G': 67, 'G#': 68, 'Ab': 68,
            'A': 69, 'A#': 70, 'Bb': 70,
            'B': 71
        }

        self.major_triad = [0, 4, 7]
        self.minor_triad = [0, 3, 7]
        self.dim_triad = [0, 3, 6]

        # Playback control
        self._playback_thread = None
        self._command_queue = Queue()
        self._is_playing = False

    def roman_to_midi_notes(self, roman_numeral: str, tonic: str, mode: str):
        """Convert Roman numeral to MIDI notes based on tonic and mode"""
        base_midi = self.notes[tonic]

        if mode == 'M':
            scale_degrees = [0, 2, 4, 5, 7, 9, 11]  # Major scale
        else:
            scale_degrees = [0, 2, 3, 5, 7, 8, 10]  # Natural minor scale

        numerals = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii'] if mode == 'm' else ['I', 'II', 'III', 'IV', 'V', 'VI',
                                                                                   'VII']
        degree = numerals.index(roman_numeral.upper() if mode == 'M' else roman_numeral.lower())

        root_midi = base_midi + scale_degrees[degree]

        if mode == 'M':
            if roman_numeral in ['I', 'IV', 'V']:
                intervals = self.major_triad
            elif roman_numeral in ['ii', 'iii', 'vi']:
                intervals = self.minor_triad
            else:
                intervals = self.dim_triad
        else:
            if roman_numeral in ['III', 'VI', 'VII']:
                intervals = self.major_triad
            elif roman_numeral in ['i', 'iv', 'v']:
                intervals = self.minor_triad
            else:
                intervals = self.dim_triad

        return [root_midi + interval for interval in intervals]

    def play_chord(self, roman_numeral: str, duration: float, tonic: str, mode: str):
        """Play a single chord"""
        try:
            if not self._is_playing:
                return

            notes = self.roman_to_midi_notes(roman_numeral, tonic, mode)
            velocity = 100

            for note in notes:
                if not self._is_playing:
                    return
                self.process.stdin.write(f"noteon 0 {note} {velocity}\n")
                self.process.stdin.flush()

            time.sleep(duration)

            for note in notes:
                self.process.stdin.write(f"noteoff 0 {note}\n")
                self.process.stdin.flush()
        except Exception as e:
            print(f"Error playing chord {roman_numeral}: {e}")
            raise

    def _play_progression_thread(self, progression, tempo, tonic, mode):
        """Internal method to play progression in a separate thread"""
        try:
            for chord_data in progression:
                if not self._is_playing:
                    break
                chord = chord_data['chord']
                duration = chord_data['duration']
                print(f"Playing: {chord} for {duration} beats in {tonic} {mode}")
                duration_seconds = (60 / tempo) * (duration / 2)

                if not self._is_playing:
                    break

                self.play_chord(chord, duration_seconds, tonic, mode)
        finally:
            self._is_playing = False

    def play_progression(self, progression, tempo=120, tonic="C", mode="M"):
        try:
            print(f"Playing progression: {progression} at {tempo} BPM")
            """Play a chord progression at the specified tempo in the given key and mode"""
            self.stop_playback()

            self._is_playing = True
            self._playback_thread = threading.Thread(
                target=self._play_progression_thread,
                args=(progression, tempo, tonic, mode)
            )
            self._playback_thread.start()
        except Exception as e:
            print(f"Error playing progression: {e}")
            raise

    def stop_playback(self):
        """Stop current playback"""
        if self._is_playing:
            self._is_playing = False
            while not self._command_queue.empty():
                self._command_queue.get()
            for note in range(128):
                self.process.stdin.write(f"noteoff 0 {note}\n")
            self.process.stdin.flush()
            if self._playback_thread:
                self._playback_thread.join()

    def cleanup(self):
        """Clean up FluidSynth resources"""
        self.stop_playback()
        if hasattr(self, 'process'):
            try:
                self.process.stdin.write("quit\n")
                self.process.stdin.flush()
                self.process.terminate()
                self.process.wait(timeout=1)
            except:
                self.process.kill()