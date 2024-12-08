import platform
import subprocess
import time
import os
import threading
import logging
from queue import Queue

logger = logging.getLogger(__name__)


class ChordPlayer:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.soundfont_path = os.path.join(current_dir, "soundfonts", "piano.sf2")

        if not os.path.exists(self.soundfont_path):
            logger.error(f"Soundfont not found at {self.soundfont_path}")
            raise FileNotFoundError(f"Soundfont not found at {self.soundfont_path}")

        logger.info(f"Using soundfont: {self.soundfont_path}")

        # Initialize FluidSynth
        self.start_fluidsynth()

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

    def start_fluidsynth(self):
        """Start or restart FluidSynth process"""
        # Check if we're running on Render
        is_render = os.environ.get('RENDER', '').lower() == 'true'

        if is_render:
            cmd = [
                "fluidsynth",
                "-a", "pulseaudio",
                "-o", "audio.pulseaudio.server=unix:/tmp/pulseaudio.socket",
                "-g", "2",  # gain
                "-r", "44100",  # sample rate
                "-c", "2",  # audio channels
                "-z", "512",  # audio buffer size
                self.soundfont_path
            ]
        else:
            # Local development settings
            system = platform.system()
            audio_driver = 'coreaudio' if system == 'Darwin' else 'pulseaudio'
            cmd = [
                "fluidsynth",
                "-a", audio_driver,
                "-g", "2",
                "-r", "44100",
                self.soundfont_path
            ]

        logger.info(f"Starting FluidSynth with command: {' '.join(cmd)}")

        try:
            if hasattr(self, 'process') and self.process:
                self.cleanup()

            env = os.environ.copy()
            if is_render:
                env['PULSE_SERVER'] = 'unix:/tmp/pulseaudio.socket'

            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

            # Check for immediate errors
            error = self.process.stderr.readline()
            if error:
                logger.warning(f"FluidSynth warning: {error.strip()}")

            logger.info("FluidSynth initialized successfully")

            # Initialize MIDI channel
            self.send_command("prog 0 0")  # Set program/instrument for channel 0

        except Exception as e:
            logger.error(f"Error starting FluidSynth: {e}")
            raise

    def send_command(self, cmd):
        """Safely send a command to FluidSynth"""
        try:
            if not self.process or self.process.poll() is not None:
                logger.warning("FluidSynth process not running, restarting...")
                self.start_fluidsynth()

            self.process.stdin.write(cmd + "\n")
            self.process.stdin.flush()

        except BrokenPipeError:
            logger.warning("Broken pipe detected, restarting FluidSynth...")
            self.start_fluidsynth()
            self.process.stdin.write(cmd + "\n")
            self.process.stdin.flush()
        except Exception as e:
            logger.error(f"Error sending command to FluidSynth: {e}")
            raise

    def play_chord(self, roman_numeral: str, duration: float, tonic: str, mode: str):
        """Play a single chord"""
        try:
            if not self._is_playing:
                return

            logger.debug(f"Playing chord: {roman_numeral} for {duration}s in {tonic} {mode}")
            notes = self.roman_to_midi_notes(roman_numeral, tonic, mode)
            velocity = 100

            # Send note on commands
            for note in notes:
                if not self._is_playing:
                    return
                self.send_command(f"noteon 0 {note} {velocity}")

            time.sleep(duration)

            # Send note off commands
            for note in notes:
                self.send_command(f"noteoff 0 {note}")

        except Exception as e:
            logger.error(f"Error playing chord {roman_numeral}: {e}")
            raise

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

    def _play_progression_thread(self, progression, tempo, tonic, mode):
        """Internal method to play progression in a separate thread"""
        try:
            for chord_data in progression:
                if not self._is_playing:
                    break
                chord = chord_data['chord']
                duration = chord_data['duration']
                logger.info(f"Playing: {chord} for {duration} beats in {tonic} {mode}")
                duration_seconds = (60 / tempo) * (duration / 2)

                if not self._is_playing:
                    break

                self.play_chord(chord, duration_seconds, tonic, mode)
        finally:
            self._is_playing = False

    def play_progression(self, progression, tempo=120, tonic="C", mode="M"):
        try:
            logger.info(f"Playing progression: {progression} at {tempo} BPM")
            self.stop_playback()

            self._is_playing = True
            self._playback_thread = threading.Thread(
                target=self._play_progression_thread,
                args=(progression, tempo, tonic, mode)
            )
            self._playback_thread.start()
        except Exception as e:
            logger.error(f"Error playing progression: {e}")
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