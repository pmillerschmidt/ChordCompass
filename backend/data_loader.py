import torch
from torch.utils.data import Dataset, DataLoader
from typing import Dict, List, Tuple, Optional
import pickle


NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

class ChordDataset(Dataset):
    def __init__(self, data_dict: Dict, sequence_length: int, chord_to_idx: Dict[str, int]):
        # Initialize chord types based on mode
        self.major_chord_types = ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°']
        self.minor_chord_types = ['i', 'ii°', 'III', 'iv', 'v', 'VI', 'VII']
        self.sequences = []
        self.chord_targets = []
        self.duration_targets = []
        for piece_name, piece_data in data_dict.items():
            result = self._process_roots(
                piece_data['root'],
                piece_data['tonic'],
                piece_data['mode']
            )
            if result is None:
                continue
            chord_sequence, duration_sequence = result
            if len(chord_sequence) >= sequence_length + 1:
                for i in range(len(chord_sequence) - sequence_length):
                    sequence = chord_sequence[i:i + sequence_length]
                    next_chord = chord_sequence[i + sequence_length]
                    next_duration = duration_sequence[i + sequence_length]
                    sequence_idx = [chord_to_idx[chord] for chord in sequence]
                    target_chord_idx = chord_to_idx[next_chord]
                    self.sequences.append(sequence_idx)
                    self.chord_targets.append(target_chord_idx)
                    self.duration_targets.append(next_duration)
        self.sequences = torch.LongTensor(self.sequences)
        self.chord_targets = torch.LongTensor(self.chord_targets)
        self.duration_targets = torch.LongTensor(self.duration_targets)

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return self.sequences[idx], self.chord_targets[idx], self.duration_targets[idx]

    def _process_roots(self, root_matrix: List[List[int]], tonic: int, mode: str) -> Optional[
        Tuple[List[str], List[int]]]:
        major_scale = [0, 2, 4, 5, 7, 9, 11]  # Scale degrees in semitones
        minor_scale = [0, 2, 3, 5, 7, 8, 10]
        scale = minor_scale if mode == 'm' else major_scale
        chord_types = self.minor_chord_types if mode == 'm' else self.major_chord_types
        chord_progression = []
        durations = []
        current_chord = None
        current_duration = 0
        for bar in root_matrix:
            for root in bar:
                interval = (root - tonic) % 12
                # non-scale tone -> None
                if interval not in scale:
                    return None
                scale_index = scale.index(interval)
                chord = chord_types[scale_index]
                if chord != current_chord:
                    if current_chord is not None:
                        chord_progression.append(current_chord)
                        durations.append(current_duration)
                    current_chord = chord
                    current_duration = 1
                else:
                    current_duration += 1
        # final chord
        if current_chord is not None:
            chord_progression.append(current_chord)
            durations.append(current_duration)
        return chord_progression, durations


def create_chord_vocabulary() -> List[str]:
    chord_types = [
        # major
        'I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°',
        # minor
        'i', 'ii°', 'III', 'iv', 'v', 'VI', 'VII'
    ]
    return chord_types


def load_dataset(path: str) -> Dict:
    with open(path, 'rb') as file:
        return pickle.load(file)

