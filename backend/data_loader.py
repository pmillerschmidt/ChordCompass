# data_loader.py
from typing import List
import csv
from pathlib import Path


class ProgressionDataLoader:
    """Loads chord progressions from various file formats"""

    @staticmethod
    def load_txt(file_path: str) -> List[str]:
        """Load progressions from txt file (one per line)"""
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]

    @staticmethod
    def load_csv(file_path: str, progression_col: str = 'Progression') -> List[str]:
        """Load progressions from CSV file"""
        progressions = []
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            if progression_col not in next(reader).keys():
                raise ValueError(f"Column '{progression_col}' not found in CSV")
            # Reset file pointer
            f.seek(0)
            next(reader)  # Skip header
            progressions = [row[progression_col] for row in reader if row[progression_col]]
        return progressions


    @classmethod
    def load(cls, file_path: str, **kwargs) -> List[str]:
        """Load progressions from a file based on its extension"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        loaders = {
            '.txt': cls.load_txt,
            '.csv': cls.load_csv
        }

        loader = loaders.get(path.suffix.lower())
        if not loader:
            raise ValueError(f"Unsupported file format: {path.suffix}")

        return loader(file_path, **kwargs)

    @staticmethod
    def validate_progression(prog: str) -> bool:
        """Validate a chord progression format"""
        if not prog:
            return False

        # Check basic format (chords separated by hyphens)
        parts = prog.split('-')
        if not parts:
            return False

        # Basic chord pattern: I, i, I#, Ib, etc.
        valid_numerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII']
        valid_accidentals = ['', '#', 'b']

        for chord in parts:
            # Remove accidental if present
            base = chord.rstrip('#b')
            # Check if it's a valid numeral (upper or lower case)
            if base.upper() not in valid_numerals:
                return False
            # Check if accidental is valid
            accidental = chord[len(base):]
            if accidental not in valid_accidentals:
                return False

        return True