import argparse
import os
from pathlib import Path
from typing import Tuple, Dict, List
import matplotlib.pyplot as plt
import numpy as np

import torch
from torch import nn
from torch.utils.data import DataLoader
import logging
from data_loader import load_dataset, create_chord_vocabulary, ChordDataset
from ChordLSTM import ChordLSTM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def plot_training_metrics(losses: List[float],
                         accuracies: List[float],
                         duration_accuracies: List[float],  # Changed from mses
                         current_epoch: int,
                         output_dir: Path):
    plt.style.use('ggplot')
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))

    epochs = np.arange(1, len(losses) + 1)

    # Plot loss
    ax1.plot(epochs, losses, 'b-', label='Total Loss')
    ax1.set_title('Training Loss')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.grid(True)
    ax1.legend()

    # Plot chord accuracy
    ax2.plot(epochs, accuracies, 'g-', label='Chord Accuracy')
    ax2.set_title('Chord Prediction Accuracy')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy')
    ax2.grid(True)
    ax2.legend()

    # Plot duration accuracy
    ax3.plot(epochs, duration_accuracies, 'r-', label='Duration Accuracy')
    ax3.set_title('Duration Prediction Accuracy')
    ax3.set_xlabel('Epoch')
    ax3.set_ylabel('Accuracy')
    ax3.grid(True)
    ax3.legend()

    plt.tight_layout()

    # Save plot
    plot_path = output_dir / f'training_metrics_epoch_{current_epoch}.png'
    print(f'Saved training metrics: {plot_path}')
    plt.savefig(plot_path)
    plt.close()


class ChordTrainer:
    def __init__(self, model: ChordLSTM, device: torch.device):
        self.model = model
        self.device = device
        # Both chord and duration now use CrossEntropyLoss
        self.chord_criterion = nn.CrossEntropyLoss()
        self.duration_criterion = nn.CrossEntropyLoss()
        self.optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='max', factor=0.5, patience=5
        )

        # Track metrics
        self.losses = []
        self.accuracies = []
        self.duration_accuracies = []  # Changed from mses

    def train_epoch(self, dataloader: DataLoader) -> Tuple[float, float, float]:
        self.model.train()
        total_loss = 0
        chord_accuracy = 0
        duration_accuracy = 0  # Changed from duration_mse

        for batch_sequences, batch_chord_targets, batch_duration_targets in dataloader:
            batch_sequences = batch_sequences.to(self.device)
            batch_chord_targets = batch_chord_targets.to(self.device)
            # Convert duration targets to 0-based indices for CrossEntropyLoss
            batch_duration_targets = (batch_duration_targets - 1).long().to(self.device)

            self.optimizer.zero_grad()
            chord_logits, duration_logits = self.model(batch_sequences)  # Now returns logits for both

            chord_loss = self.chord_criterion(chord_logits, batch_chord_targets)
            duration_loss = self.duration_criterion(duration_logits, batch_duration_targets)
            combined_loss = chord_loss + duration_loss

            combined_loss.backward()
            self.optimizer.step()

            total_loss += combined_loss.item()

            # Calculate accuracies for both predictions
            chord_pred = torch.argmax(chord_logits, dim=1)
            duration_pred = torch.argmax(duration_logits, dim=1)

            chord_accuracy += (chord_pred == batch_chord_targets).float().mean().item()
            duration_accuracy += (duration_pred == batch_duration_targets).float().mean().item()

        num_batches = len(dataloader)
        # Store metrics
        avg_loss = total_loss / num_batches
        avg_chord_accuracy = chord_accuracy / num_batches
        avg_duration_accuracy = duration_accuracy / num_batches

        self.losses.append(avg_loss)
        self.accuracies.append(avg_chord_accuracy)
        self.duration_accuracies.append(avg_duration_accuracy)  # Changed from mses

        return avg_loss, avg_chord_accuracy, avg_duration_accuracy

    def save_checkpoint(self, path: Path, epoch: int, vocab: Dict):
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'vocab': vocab
        }
        torch.save(checkpoint, path)
        logger.info(f"Saved checkpoint to {path}")

    def load_checkpoint(self, path: Path) -> Tuple[int, Dict]:
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        return checkpoint['epoch'], checkpoint['vocab']


def main():
    parser = argparse.ArgumentParser(description='Train Chord Progression Model')
    parser.add_argument('--data_path', type=str, default='dataset.pkl', help='Path to dataset pickle file')
    parser.add_argument('--output_dir', type=str, default='checkpoints/', help='Directory to save checkpoints')
    parser.add_argument('--sequence_length', type=int, default=3, help='Length of input sequences')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size')
    parser.add_argument('--num_epochs', type=int, default=50, help='Number of epochs')
    parser.add_argument('--hidden_dim', type=int, default=64, help='Hidden dimension')
    parser.add_argument('--checkpoint', type=str, help='Path to checkpoint to resume from')

    args = parser.parse_args()

    # Setup device
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize vocabulary and dataset
    chord_types = create_chord_vocabulary()
    chord_to_idx = {chord: idx for idx, chord in enumerate(chord_types)}
    dataset = load_dataset(args.data_path)

    # Create model and trainer
    model = ChordLSTM(
        vocab_size=len(chord_types),
        hidden_dim=args.hidden_dim
    ).to(device)

    trainer = ChordTrainer(model, device)

    # Load checkpoint if specified
    start_epoch = 0
    if args.checkpoint:
        start_epoch, _ = trainer.load_checkpoint(Path(args.checkpoint))
        logger.info(f"Resumed from epoch {start_epoch}")

    # Create dataset and dataloader
    chord_dataset = ChordDataset(dataset, args.sequence_length, chord_to_idx)
    logger.info(f"Dataset size: {len(chord_dataset)} sequences")

    dataloader = DataLoader(
        chord_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=4
    )

    # Training loop
    for epoch in range(start_epoch, args.num_epochs):
        loss, chord_acc, duration_acc = trainer.train_epoch(dataloader)
        logger.info(
            f"Epoch [{epoch + 1}/{args.num_epochs}] "
            f"Loss: {loss:.4f} "
            f"Chord Accuracy: {chord_acc:.4f} "
            f"Duration Accuracy: {duration_acc:.4f}"
        )

        # Save checkpoint and create visualization every 10 epochs
        if (epoch + 1) % 10 == 0:
            checkpoint_path = output_dir / f"checkpoint_epoch_{epoch + 1}.pt"
            trainer.save_checkpoint(checkpoint_path, epoch + 1, chord_to_idx)
            # plot
            plot_training_metrics(
                trainer.losses,
                trainer.accuracies,
                trainer.duration_accuracies,  # Changed from mses
                epoch + 1,
                output_dir
            )

    # save final model
    trainer.save_checkpoint(output_dir / 'final_model.pt', args.num_epochs, chord_to_idx)


if __name__ == "__main__":
    main()