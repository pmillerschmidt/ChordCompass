import torch
import torch.nn as nn
from typing import List, Dict


class ChordLSTM(nn.Module):
    def __init__(self, vocab_size: int, embedding_dim: int, hidden_dim: int):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, num_layers=2, batch_first=True)
        self.fc = nn.Linear(hidden_dim, vocab_size)

    def forward(self, x):
        embedded = self.embedding(x)
        lstm_out, _ = self.lstm(embedded)
        return self.fc(lstm_out[:, -1, :])


class ChordProgressionModel:
    def __init__(self, sequence_length=3):
        self.sequence_length = sequence_length
        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
        print(f"Using device: {self.device}")

        # Initialize chord vocabulary
        self.chord_types = self._initialize_chord_types()
        self.chord_to_idx = {chord: idx for idx, chord in enumerate(self.chord_types)}
        self.idx_to_chord = {idx: chord for chord, idx in self.chord_to_idx.items()}

        # Initialize model
        self.model = ChordLSTM(
            vocab_size=len(self.chord_types),
            embedding_dim=16,
            hidden_dim=32
        ).to(self.device)

        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = torch.optim.Adam(self.model.parameters())

    def _initialize_chord_types(self) -> List[str]:
        """Initialize the vocabulary of chord symbols"""
        chord_types = []
        basic_numerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII']

        # Add major and minor chords with accidentals
        for numeral in basic_numerals:
            # Major chords
            chord_types.extend([numeral, f"{numeral}#", f"{numeral}b"])
            # Minor chords
            lower = numeral.lower()
            chord_types.extend([lower, f"{lower}#", f"{lower}b"])

        return chord_types

    def save_model(self, path: str):
        """Save model state and vocabulary"""
        state = {
            'model_state': self.model.state_dict(),
            'chord_to_idx': self.chord_to_idx,
            'sequence_length': self.sequence_length
        }
        torch.save(state, path)

    def load_model(self, path: str):
        """Load model state and vocabulary"""
        state = torch.load(path, map_location=self.device)
        self.chord_to_idx = state['chord_to_idx']
        self.idx_to_chord = {idx: chord for chord, idx in self.chord_to_idx.items()}
        self.sequence_length = state['sequence_length']
        self.model.load_state_dict(state['model_state'])