import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Optional

import torch
import logging
from ChordLSTM import ChordLSTM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChordGenerator:
    def __init__(self, model: ChordLSTM, device: torch.device, chord_to_idx: dict):
        self.model = model
        self.device = device
        self.chord_to_idx = chord_to_idx
        self.idx_to_chord = {idx: chord for chord, idx in chord_to_idx.items()}

    def generate_progression(self, seed_progression: Optional[List[str]] = None, length: int = 8, temperature: float = 1.0) -> List[Tuple[str, int]]:
        if seed_progression is None:
            # seed with root
            seed_progression = ['I'] * 3
        self.model.eval()
        seed_indices = [self.chord_to_idx.get(chord, 0) for chord in seed_progression]
        current_sequence = torch.LongTensor([seed_indices]).to(self.device)
        generated_progression = []
        with torch.no_grad():
            for _ in range(length):
                chord_logits, duration_logits = self.model(current_sequence)
                # temperature
                chord_logits = chord_logits / temperature
                duration_logits = duration_logits / temperature
                # sample chord
                chord_probs = torch.softmax(chord_logits, dim=1)
                next_chord_idx = torch.multinomial(chord_probs[0], 1).item()
                next_chord = self.idx_to_chord[next_chord_idx]
                # sample dur
                duration_probs = torch.softmax(duration_logits, dim=1)
                duration_idx = torch.multinomial(duration_probs[0], 1).item()
                next_duration = duration_idx + 1
                generated_progression.append((next_chord, next_duration))
                # update
                current_sequence = torch.cat([
                    current_sequence[:, 1:],
                    torch.LongTensor([[next_chord_idx]]).to(self.device)
                ], dim=1)
        return generated_progression


def load_model(checkpoint_path: Path, device: torch.device) -> Tuple[ChordLSTM, Dict]:
    checkpoint = torch.load(checkpoint_path, map_location=device)
    chord_to_idx = checkpoint['vocab']
    model = ChordLSTM(
        vocab_size=len(chord_to_idx),
        hidden_dim=64
    ).to(device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    return model, chord_to_idx


def main():
    parser = argparse.ArgumentParser(description='Generate Chord Progressions')
    parser.add_argument('--checkpoint', type=str, required=True, help='Path to model checkpoint')
    parser.add_argument('--seed_progression', type=str, nargs='+', default=None, help='Seed progression')
    parser.add_argument('--length', type=int, default=4,
                        help='Length of progression to generate')
    parser.add_argument('--temperature', type=float, default=1.0,
                        help='Sampling temperature (higher = more random)')
    args = parser.parse_args()
    # setup
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    logger.info(f"Using device: {device}")
    # model and vocabulary
    model, chord_to_idx = load_model(Path(args.checkpoint), device)
    generator = ChordGenerator(model, device, chord_to_idx)
    # gen progression
    progression = generator.generate_progression(
        args.seed_progression,
        length=args.length,
        temperature=args.temperature
    )
    print("\nGenerated Progression:")
    print("---------------------")
    total_duration = 0
    for i, (chord, duration) in enumerate(progression, 1):
        total_eighth_notes = duration
        total_duration += duration / 8.0  # Convert eighth notes to bars
        print(f"{i}. {chord:<4} (duration: {duration} eighth notes, {duration/8:.2f} bars)")
    print(f"\nTotal duration: {total_duration:.2f} bars")


if __name__ == "__main__":
    main()
