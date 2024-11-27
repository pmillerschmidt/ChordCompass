import subprocess
import time
import os


class ChordPlayer:
    def __init__(self):
        self.soundfont_path = os.path.expanduser("~/soundfonts/piano.sf2")
        if not os.path.exists(self.soundfont_path):
            raise FileNotFoundError(f"Soundfont not found at {self.soundfont_path}")

        print(f"Using soundfont: {self.soundfont_path}")

        # Simpler FluidSynth initialization
        cmd = [
            "fluidsynth",
            "-a", "coreaudio",
            self.soundfont_path
        ]

        print(f"Starting FluidSynth with command: {' '.join(cmd)}")

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        time.sleep(1)  # Wait for initialization

        if self.process.poll() is not None:
            error = self.process.stderr.read()
            raise RuntimeError(f"FluidSynth failed to start: {error}")

        print("FluidSynth initialized successfully")

        self.scale = {
            'C': 60,  # I
            'D': 62,  # II
            'E': 64,  # III
            'F': 65,  # IV
            'G': 67,  # V
            'A': 69,  # VI
            'B': 71  # VII
        }

        self.major_triad = [0, 4, 7]
        self.minor_triad = [0, 3, 7]
        self.dim_triad = [0, 3, 6]

    def roman_to_midi_notes(self, roman_numeral: str):
        """Convert Roman numeral to MIDI notes"""
        # Remove accidentals for base note
        base_numeral = roman_numeral.rstrip('#b')

        # Determine root note and chord quality
        numerals = {
            'I': 'C', 'II': 'D', 'III': 'E', 'IV': 'F',
            'V': 'G', 'VI': 'A', 'VII': 'B'
        }

        root = numerals[base_numeral.upper()]
        root_midi = self.scale[root]

        # Determine chord quality based on numeral case
        if base_numeral.isupper():
            intervals = self.major_triad
        else:
            intervals = self.minor_triad if base_numeral != 'vii' else self.dim_triad

        return [root_midi + interval for interval in intervals]

    def play_chord(self, roman_numeral: str, duration: float = 1.0):
        """Play a single chord"""
        try:
            notes = self.roman_to_midi_notes(roman_numeral)
            velocity = 100  # Volume (0-127)

            # Start notes
            for note in notes:
                self.process.stdin.write(f"noteon 0 {note} {velocity}\n")
                self.process.stdin.flush()

            time.sleep(duration)

            # Stop notes
            for note in notes:
                self.process.stdin.write(f"noteoff 0 {note}\n")
                self.process.stdin.flush()
        except Exception as e:
            print(f"Error playing chord {roman_numeral}: {e}")
            raise

    def play_progression(self, progression, tempo=120):
        """Play a chord progression at the specified tempo"""
        try:
            duration = 60 / tempo  # Convert tempo to seconds per beat
            for chord in progression:
                print(f"Playing: {chord}")
                self.play_chord(chord, duration)
        except Exception as e:
            print(f"Error playing progression: {e}")
            raise

    def test_sound(self):
        """Test function to play a simple C major chord"""
        try:
            print("Testing sound output...")
            notes = [60, 64, 67]  # C major chord
            velocity = 100

            for note in notes:
                print(f"Playing note {note}")
                self.process.stdin.write(f"noteon 0 {note} {velocity}\n")
                self.process.stdin.flush()

            time.sleep(2)

            for note in notes:
                self.process.stdin.write(f"noteoff 0 {note}\n")
                self.process.stdin.flush()

        except Exception as e:
            print(f"Error during test: {e}")
            raise

    def cleanup(self):
        """Clean up FluidSynth resources"""
        if hasattr(self, 'process'):
            try:
                self.process.stdin.write("quit\n")
                self.process.stdin.flush()
                self.process.terminate()
                self.process.wait(timeout=1)
            except:
                self.process.kill()


# Test script
if __name__ == "__main__":
    try:
        player = ChordPlayer()
        print("\nTesting single chord...")
        player.play_chord("I", 1.0)

        print("\nTesting progression...")
        player.play_progression(["I", "IV", "V", "I"], tempo=120)

    finally:
        player.cleanup()