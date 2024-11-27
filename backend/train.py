# train.py
import torch
from ChordLSTM import ChordProgressionModel
from data_loader import ProgressionDataLoader
from typing import List
import argparse
from pathlib import Path


def parse_progression(prog_string: str) -> List[str]:
    """Convert progression string to list of chords"""
    return [chord for chord in prog_string.split('-') if chord]


def prepare_sequences(progressions: List[List[str]], model: ChordProgressionModel):
    """Prepare sequences for training"""
    X, y = [], []

    for prog in progressions:
        # Convert chords to indices
        chord_seq = [model.chord_to_idx.get(chord, 0) for chord in prog]

        # Create sequences
        for i in range(len(chord_seq) - model.sequence_length):
            X.append(chord_seq[i:i + model.sequence_length])
            y.append(chord_seq[i + model.sequence_length])

    return torch.LongTensor(X).to(model.device), torch.LongTensor(y).to(model.device)


def train_model(model: ChordProgressionModel, progression_strings: List[str], epochs: int = 100):
    """Train the model on progression strings"""
    # Parse all progressions
    progressions = [parse_progression(prog) for prog in progression_strings]

    # Prepare sequences
    X, y = prepare_sequences(progressions, model)

    print(f"Training on {len(progressions)} progressions ({len(X)} sequences)")

    # Training loop
    model.model.train()
    for epoch in range(epochs):
        model.optimizer.zero_grad()
        output = model.model(X)
        loss = model.criterion(output, y)
        loss.backward()
        model.optimizer.step()

        if (epoch + 1) % 10 == 0:
            print(f'Epoch [{epoch + 1}/{epochs}], Loss: {loss.item():.4f}')


def main():
    parser = argparse.ArgumentParser(description='Train chord progression model')
    parser.add_argument('--data_path', type=str, default='progressions.csv', help='Path to data file')
    parser.add_argument('--epochs', type=int, default=100, help='Number of training epochs')
    parser.add_argument('--save_path', type=str, default='chord_model.pth', help='Path to save model')
    parser.add_argument('--progression_col', type=str, default='Progression',
                        help='Column name for progressions in CSV file')
    args = parser.parse_args()

    # Load data
    print(f"Loading data from {args.data_path}")
    try:
        loader = ProgressionDataLoader()
        progressions = loader.load(args.data_path, progression_col=args.progression_col)
        # Validate progressions
        valid_progressions = [prog for prog in progressions if loader.validate_progression(prog)]
        invalid_count = len(progressions) - len(valid_progressions)
        if invalid_count > 0:
            print(f"Warning: {invalid_count} invalid progressions were filtered out")
        if not valid_progressions:
            raise ValueError("No valid progressions found in data file")
        print(f"Loaded {len(valid_progressions)} valid progressions")
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    # Initialize and train model
    print("\nInitializing model...")
    model = ChordProgressionModel(sequence_length=3)

    print("\nTraining model...")
    train_model(model, valid_progressions, epochs=args.epochs)

    # Save model
    print(f"\nSaving model to {args.save_path}")
    model.save_model(args.save_path)


if __name__ == "__main__":
    main()