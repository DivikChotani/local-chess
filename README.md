# Local Chess - React × Stockfish Chess Game

A modern, feature-rich chess application built with React and Python Flask, featuring Stockfish engine integration, position analysis, and a beautiful UI.

## Features

- **Play against Stockfish**: Configure engine strength (ELO 800-3000) and think time
- **Dual Input Methods**: Click-to-move and drag-and-drop piece movement
- **Real-time Analysis**: Get centipawn evaluation for any position
- **Move Hints**: Get top 3 best moves with evaluations
- **Game History**: View and manage previous games
- **Move History**: Track all moves in the current game
- **Responsive Design**: Works on desktop and mobile devices
- **Beautiful UI**: Modern dark theme with smooth animations

## Architecture

- **Frontend**: React + TypeScript + Vite
- **Backend**: Python Flask + Stockfish engine
- **Chess Logic**: python-chess library
- **UI Components**: react-chessboard

## Prerequisites

- **Node.js** (v16 or higher)
- **Python** (v3.8 or higher)
- **Stockfish** chess engine
- **npm** or **yarn** package manager


### 1. Clone the Repository
```bash
git clone
cd local-chess
```

### 2. Install Dependencies

#### Backend Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

#### Frontend Setup
```bash
cd frontend
npm install
```

### 3. Install Stockfish

#### macOS (using Homebrew)
```bash
brew install stockfish
```

### 4. Run the Application

#### Option 1: Use the Shell Script (Recommended)
```bash
# Make the script executable
chmod +x run.sh

# Run the application
./run.sh
```

#### Option 2: Manual Setup
```bash
# Terminal 1: Start the backend
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python local_chess.py

# Terminal 2: Start the frontend
cd frontend
npm run dev
```

### 5. Access the Application
Open your browser and navigate to: `http://localhost:5173`

## How to Play

1. **Configure Your Opponent**:
   - Set Engine Strength (ELO): 800-3000 (higher = stronger)
   - Set Think Time: 0.05-5 seconds (longer = stronger moves)

2. **Start a Game**:
   - Click "Start New Game" to begin
   - You play as White, Stockfish plays as Black

3. **Make Moves**:
   - **Click-to-move**: Click a piece, then click a destination square

4. **Use Features**:
   - **Analyze Position**: Get centipawn evaluation for current position
   - **Hint**: Get top 3 best moves
   - **Move History**: View all moves in the current game
   - **Game History**: Browse previous games

## Development

### Project Structure
```
local-chess/
├── backend/
│   ├── local_chess.py      # Flask server with Stockfish integration
│   ├── requirements.txt    # Python dependencies
│   └── chess-games.db     # SQLite database for game history
├── frontend/
│   ├── src/
│   │   ├── App.tsx        # Main React component
│   │   └── App.css        # Styles
│   ├── package.json       # Node.js dependencies
│   └── vite.config.ts     # Vite configuration
├── run.sh                 # Shell script to run the entire project
└── README.md             # This file
```

### Backend API Endpoints

- `GET /initialize-board` - Start new game
- `POST /post-move` - Make a player move
- `POST /engine-move` - Get engine response
- `POST /analyze-position` - Analyze current position
- `GET /best-moves` - Get top moves for hints
- `GET /game-history` - Get previous games

### Frontend Components

- **App.tsx**: Main application component
- **AnalysisPanel**: Position evaluation display
- **GameHistoryPanel**: Game history browser
- **Chessboard**: Interactive chess board

## Configuration

### Engine Settings
- **ELO Range**: 800-3000 (800 = Beginner, 2800 = Master)
- **Think Time**: 0.05-5 seconds (affects move strength)

### Stockfish Path
If Stockfish is not in the default location, update the path in `backend/local_chess.py`:
```python
engine = chess.engine.SimpleEngine.popen_uci("/path/to/stockfish")
```



## Dependencies

### Backend
- `flask`: Web framework
- `flask-cors`: Cross-origin resource sharing
- `chess`: Python chess library
- `chess-engine`: Stockfish integration

### Frontend
- `react`: UI library
- `react-chessboard`: Chess board component
- `chess.js`: Chess logic
- `axios`: HTTP client
- `vite`: Build tool



- [Stockfish](https://stockfishchess.org/) - Chess engine
- [python-chess](https://python-chess.readthedocs.io/) - Python chess library
- [react-chessboard](https://github.com/Clariity/react-chessboard) - React chess component
- [chess.js](https://github.com/jhlywa/chess.js) - JavaScript chess library

