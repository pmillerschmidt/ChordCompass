import torch.nn as nn

class ChordLSTM(nn.Module):
    def __init__(self, vocab_size: int, hidden_dim: int):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, hidden_dim)
        self.lstm = nn.LSTM(
            hidden_dim,
            hidden_dim * 2,  # Increase hidden dimension
            num_layers=3,    # Add more layers
            batch_first=True,
            dropout=0.1      # Reduce dropout
        )
        self.dropout = nn.Dropout(0.1)
        self.chord_head = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, vocab_size)
        )
        self.duration_head = nn.Linear(hidden_dim * 2, 8)

    def forward(self, x):
        embedded = self.dropout(self.embedding(x))
        lstm_out, _ = self.lstm(embedded)
        last_hidden = lstm_out[:, -1, :]

        chord_logits = self.chord_head(last_hidden)
        duration_logits = self.duration_head(last_hidden)  # Now outputs logits for 8 classes

        return chord_logits, duration_logits
