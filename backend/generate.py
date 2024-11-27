# generate.py
import torch
import numpy as np
from player import ChordPlayer
from ChordLSTM import ChordProgressionModel
import argparse


def generate_progression(seed_progression: str, length: int = 8, model_path: str = 'chord_model.pth'):
    """Generate a new progression from a seed"""
    # Initialize model and load weights
    model = ChordProgressionModel()
    model.load_model(model_path)  # Load the saved weights

    model.model.eval()  # Set to evaluation mode

    # Parse seed
    if isinstance(seed_progression, str):
        seed_progression = [chord for chord in seed_progression.split('-') if chord]

    if len(seed_progression) < model.sequence_length:
        print(f"Warning: Seed progression too short, padding with I")
        seed_progression = ['I'] * (model.sequence_length - len(seed_progression)) + seed_progression

    # Convert seed to indices
    generated = [model.chord_to_idx.get(chord, 0) for chord in seed_progression]

    # Generate new chords
    with torch.no_grad():
        for _ in range(length - len(seed_progression)):
            sequence = torch.LongTensor([generated[-model.sequence_length:]]).to(model.device)
            output = model.model(sequence)
            probs = torch.softmax(output, dim=1).cpu().numpy()[0]

            # Add some randomness
            probs = np.power(probs, 1.2)
            probs /= probs.sum()

            next_chord = np.random.choice(len(model.chord_types), p=probs)
            generated.append(next_chord)

    # Convert back to chord symbols
    return [model.idx_to_chord[idx] for idx in generated]


if __name__ == "__main__":
    # Test generation
    progression = generate_progression("I-VI#-ii", length=8)
    print("Generated progression:", "-".join(progression))


def main():
    parser = argparse.ArgumentParser(description='Generate chord progressions')
    parser.add_argument('--model_path', type=str, default='chord_model.pth', help='Path to trained model')
    parser.add_argument('--seed', type=str, default='I-VI#-ii', help='Seed progression')
    parser.add_argument('--length', type=int, default=8, help='Length of generated progression')
    parser.add_argument('--duration', type=float, default=1.0, help='Duration per chord in seconds')
    parser.add_argument('--play', action='store_true', help='Play the progression')
    args = parser.parse_args()

    # Load model
    print(f"Loading model from {args.model_path}")
    model = ChordProgressionModel()
    model.load_model(args.model_path)

    # Generate progression
    print(f"\nGenerating progression from seed: {args.seed}")
    progression = generate_progression(seed_progression=args.seed, length=args.length, model_path=args.model_path)
    print("Generated progression:", "-".join(progression))

    # Play progression if requested
    if args.play:
        try:
            player = ChordPlayer()
            print("\nPlaying progression in C major...")
            player.play_progression(progression, args.duration)
            player.cleanup()
        except Exception as e:
            print(f"Error playing progression: {e}")
            print("Make sure you have a MIDI output device available.")

if __name__ == "__main__":
    main()