# ChordCompass

ChordCompass is a web application that generates and plays musical chord progressions using machine learning. The application features a Python backend with PyTorch for progression generation and FluidSynth for audio playback, paired with a React frontend for user interaction.

## Setup

### Prerequisites
- Python 3.9+
- Node.js
- FluidSynth
- A SoundFont file (.sf2)

### Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt

# Install FluidSynth (macOS)
brew install fluid-synth
```

### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

### SoundFont Setup
1. Create a soundfonts directory in your home folder:
```bash
mkdir -p ~/soundfonts
```

2. Place your .sf2 file in the soundfonts directory (e.g., piano.sf2)

## Running the Application

1. Start the backend server:
```bash
# From the backend directory
source venv/bin/activate
uvicorn main:app --reload
```

2. Start the frontend development server:
```bash
# From the frontend directory
npm start
```

3. Open `http://localhost:3000` in your browser

## Usage

1. Enter a seed progression using Roman numerals (e.g., "I-IV-V")
2. Adjust the desired length of the generated progression
3. Click "Generate" to create a new progression
4. Use the player controls to:
   - Adjust tempo
   - Play/pause the progression
   - Visualize the current chord

## Project Structure

```
ChordCompass/
├── backend/
│   ├── main.py           # FastAPI server
│   ├── model.py          # ML model definition
│   ├── player.py         # Audio playback
│   ├── generate.py       # Generation logic
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/   # React components
    │   ├── services/     # API services
    │   └── App.js
    └── package.json
```

## Technology Stack

- **Backend**
  - FastAPI
  - PyTorch
  - FluidSynth
  
- **Frontend**
  - React
  - Tailwind CSS
  - shadcn/ui

## License

MIT