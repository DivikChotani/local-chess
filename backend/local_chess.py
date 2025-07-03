from flask import Flask, request, jsonify
import chess
import chess.engine
import chess.pgn
import sqlite3
from flask_cors import CORS
from datetime import datetime
import json
import os
import threading
import logging
from contextlib import contextmanager
import signal
import sys
from typing import Optional, Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Allow all common development origins
CORS(app, origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174"
])

# Global variables
board: Optional[chess.Board] = None
engine: Optional[chess.engine.SimpleEngine] = None
current_game_id: Optional[int] = None
db_lock = threading.Lock()

# Configuration
STOCKFISH_PATH = "/opt/homebrew/bin/stockfish"  # Update this path as needed
DATABASE_PATH = "chess-games.db"
DEFAULT_TIME_LIMIT = 0.1
MIN_ELO = 800
MAX_ELO = 3000

# Database schema
CREATE_GAMES_TABLE = """
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    pgn TEXT,
    result TEXT,
    white_player TEXT DEFAULT 'Human',
    black_player TEXT DEFAULT 'Stockfish',
    engine_elo INTEGER,
    engine_time_limit REAL,
    opening_name TEXT,
    total_moves INTEGER DEFAULT 0
)
"""

CREATE_MOVES_TABLE = """
CREATE TABLE IF NOT EXISTS moves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER,
    move_number INTEGER,
    move_notation TEXT,
    fen_after TEXT,
    evaluation REAL,
    best_move TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games (id)
)
"""

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize database tables"""
    with get_db() as conn:
        conn.execute(CREATE_GAMES_TABLE)
        conn.execute(CREATE_MOVES_TABLE)
        conn.commit()
    logger.info("Database initialized")

def init_engine():
    """Initialize Stockfish engine"""
    global engine
    try:
        if os.path.exists(STOCKFISH_PATH):
            engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
            logger.info("Stockfish engine initialized")
        else:
            logger.error(f"Stockfish not found at {STOCKFISH_PATH}")
            engine = None
    except Exception as e:
        logger.error(f"Failed to initialize Stockfish: {e}")
        engine = None

def create_new_game(engine_elo: int = 1320, engine_time: float = 0.1) -> int:
    """Create a new game in the database"""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO games (engine_elo, engine_time_limit) VALUES (?, ?)",
            (engine_elo, engine_time)
        )
        conn.commit()
        return cursor.lastrowid

def save_move(game_id: int, move_num: int, move_notation: str, fen: str, 
              evaluation: Optional[float] = None, best_move: Optional[str] = None):
    """Save a move to the database"""
    with db_lock:
        with get_db() as conn:
            conn.execute(
                """INSERT INTO moves 
                   (game_id, move_number, move_notation, fen_after, evaluation, best_move) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (game_id, move_num, move_notation, fen, evaluation, best_move)
            )
            conn.commit()

def update_game_result(game_id: int, result: str, pgn: str, total_moves: int):
    """Update game result in database"""
    with get_db() as conn:
        conn.execute(
            """UPDATE games 
               SET end_time = CURRENT_TIMESTAMP, result = ?, pgn = ?, total_moves = ? 
               WHERE id = ?""",
            (result, pgn, total_moves, game_id)
        )
        conn.commit()

def get_opening_name(board: chess.Board) -> Optional[str]:
    """Get opening name based on current position"""
    # This is a simplified version - you could expand with a proper opening database
    move_count = len(board.move_stack)
    if move_count < 4:
        return None
    
    # Common openings (simplified)
    fen = board.fen()
    if "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR" in fen:
        return "King's Pawn Opening"
    elif "rnbqkbnr/pppp1ppp/8/4p3/3PP3/8/PPP2PPP/RNBQKBNR" in fen:
        return "Queen's Gambit"
    # Add more openings as needed
    return "Unknown Opening"

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "engine_available": engine is not None,
        "database": os.path.exists(DATABASE_PATH)
    })

@app.route('/initialize-board', methods=['GET'])
def initialize_board():
    """Initialize a new chess game"""
    global board, current_game_id
    
    try:
        board = chess.Board()
        
        # Get optional parameters
        engine_elo = request.args.get('elo', 1320, type=int)
        engine_time = request.args.get('time', 0.1, type=float)
        
        # Validate parameters
        engine_elo = max(MIN_ELO, min(MAX_ELO, engine_elo))
        engine_time = max(0.05, min(5.0, engine_time))
        
        # Create new game in database
        current_game_id = create_new_game(engine_elo, engine_time)
        
        logger.info(f"New game started (ID: {current_game_id}, ELO: {engine_elo})")
        
        return jsonify({
            "fen": board.fen(),
            "game_id": current_game_id,
            "turn": "white",
            "legal_moves": [move.uci() for move in board.legal_moves]
        })
    except Exception as e:
        logger.error(f"Error initializing board: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/post-move', methods=['POST'])
def post_move():
    """Process a player's move"""
    global board
    
    if board is None:
        return jsonify({"error": "No active game"}), 400
    
    try:
        data = request.get_json()
        if not data or 'new-move' not in data:
            return jsonify({"error": "Missing move data"}), 400
        
        move_uci = data['new-move']
        
        # Validate and make move
        try:
            move = chess.Move.from_uci(move_uci)
            if move not in board.legal_moves:
                return jsonify({"error": "Illegal move"}), 400
        except ValueError:
            return jsonify({"error": "Invalid move format"}), 400
        
        # Get move notation before making the move
        san = board.san(move)
        move_num = len(board.move_stack) // 2 + 1
        
        # Make the move
        board.push(move)
        
        # Evaluate position if engine is available
        evaluation = None
        best_move = None
        if engine:
            try:
                info = engine.analyse(board, chess.engine.Limit(time=0.1))
                score = info.get('score')
                if score:
                    evaluation = score.relative.score(mate_score=10000) / 100.0
                if 'pv' in info and info['pv']:
                    best_move = info['pv'][0].uci()
            except Exception as e:
                logger.warning(f"Engine analysis failed: {e}")
        
        # Save move to database
        if current_game_id:
            save_move(current_game_id, move_num, san, board.fen(), evaluation, best_move)
        
        # Check game state
        game_over = board.is_game_over()
        result_data = {
            "fen": board.fen(),
            "game_over": game_over,
            "turn": "black" if board.turn else "white",
            "legal_moves": [m.uci() for m in board.legal_moves],
            "last_move": move_uci,
            "move_history": [m.uci() for m in board.move_stack]
        }
        
        if game_over:
            result = board.result()
            result_data["result"] = result
            result_data["termination"] = get_termination_reason(board)
            
            # Generate PGN
            pgn_game = chess.pgn.Game()
            pgn_game.headers["Event"] = "Online Game"
            pgn_game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
            pgn_game.headers["White"] = "Human"
            pgn_game.headers["Black"] = "Stockfish"
            pgn_game.headers["Result"] = result
            
            node = pgn_game
            for move in board.move_stack:
                node = node.add_variation(move)
            
            pgn_str = str(pgn_game)
            
            # Update database
            if current_game_id:
                update_game_result(current_game_id, result, pgn_str, len(board.move_stack))
            
            result_data["pgn"] = pgn_str
        
        return jsonify(result_data)
        
    except Exception as e:
        logger.error(f"Error processing move: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/engine-move', methods=['POST'])
def engine_move():
    """Make an engine move"""
    global board
    
    if board is None:
        return jsonify({"error": "No active game"}), 400
    
    if engine is None:
        return jsonify({"error": "Engine not available"}), 503
    
    try:
        data = request.get_json()
        engine_elo = data.get('elo', 1320)
        engine_time = float(data.get('time', 0.1))
        
        # Validate parameters
        engine_elo = max(MIN_ELO, min(MAX_ELO, engine_elo))
        engine_time = max(0.05, min(5.0, engine_time))
        
        # Configure engine strength
        engine.configure({
            "UCI_LimitStrength": True,
            "UCI_Elo": engine_elo
        })
        
        # Get engine move
        result = engine.play(board, chess.engine.Limit(time=engine_time))
        move = result.move
        
        # Get move notation
        san = board.san(move)
        move_num = len(board.move_stack) // 2 + 1
        
        # Make the move
        board.push(move)
        
        # Evaluate position
        evaluation = None
        best_move = None
        try:
            info = engine.analyse(board, chess.engine.Limit(time=0.1))
            score = info.get('score')
            if score:
                evaluation = score.relative.score(mate_score=10000) / 100.0
            if 'pv' in info and info['pv']:
                best_move = info['pv'][0].uci()
        except Exception as e:
            logger.warning(f"Engine analysis failed: {e}")
        
        # Save move to database
        if current_game_id:
            save_move(current_game_id, move_num, san, board.fen(), evaluation, best_move)
        
        # Check game state
        game_over = board.is_game_over()
        result_data = {
            "fen": board.fen(),
            "game_over": game_over,
            "turn": "white" if board.turn else "black",
            "legal_moves": [m.uci() for m in board.legal_moves],
            "last_move": move.uci(),
            "engine_move": san,
            "move_history": [m.uci() for m in board.move_stack]
        }
        
        if game_over:
            result = board.result()
            result_data["result"] = result
            result_data["termination"] = get_termination_reason(board)
            
            # Generate and save PGN
            pgn_game = chess.pgn.Game()
            pgn_game.headers["Event"] = "Online Game"
            pgn_game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
            pgn_game.headers["White"] = "Human"
            pgn_game.headers["Black"] = f"Stockfish ({engine_elo})"
            pgn_game.headers["Result"] = result
            
            node = pgn_game
            for move in board.move_stack:
                node = node.add_variation(move)
            
            pgn_str = str(pgn_game)
            
            if current_game_id:
                update_game_result(current_game_id, result, pgn_str, len(board.move_stack))
            
            result_data["pgn"] = pgn_str
        
        return jsonify(result_data)
        
    except Exception as e:
        logger.error(f"Error making engine move: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/best-moves', methods=['GET'])
def get_best_moves():
    """Get multiple best moves with evaluation"""
    if board is None:
        return jsonify({"error": "No active game"}), 400
    
    if engine is None:
        return jsonify({"error": "Engine not available"}), 503
    
    try:
        multipv = request.args.get('multipv', 5, type=int)
        time_limit = request.args.get('time', 0.5, type=float)
        
        # Analyze position
        info = engine.analyse(board, chess.engine.Limit(time=time_limit), multipv=multipv)
        
        moves = []
        for i, variant in enumerate(info):
            if 'pv' not in variant or not variant['pv']:
                continue
            
            move = variant['pv'][0]
            score = variant.get('score')
            
            move_data = {
                "move": move.uci(),
                "san": board.san(move),
                "rank": i + 1
            }
            
            if score:
                if score.is_mate():
                    move_data["mate_in"] = score.relative.mate()
                else:
                    move_data["evaluation"] = score.relative.score(mate_score=10000) / 100.0
            
            # Get line continuation
            if len(variant['pv']) > 1:
                line = []
                temp_board = board.copy()
                for m in variant['pv'][:5]:  # First 5 moves of the line
                    line.append(temp_board.san(m))
                    temp_board.push(m)
                move_data["line"] = " ".join(line)
            
            moves.append(move_data)
        
        return jsonify({
            "best_moves": moves,
            "position_type": get_position_type(board),
            "turn": "white" if board.turn else "black"
        })
        
    except Exception as e:
        logger.error(f"Error getting best moves: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/game-history', methods=['GET'])
def get_game_history():
    """Get list of past games"""
    try:
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        with get_db() as conn:
            games = conn.execute(
                """SELECT id, start_time, end_time, result, white_player, black_player, 
                          engine_elo, total_moves, opening_name
                   FROM games 
                   WHERE end_time IS NOT NULL
                   ORDER BY start_time DESC 
                   LIMIT ? OFFSET ?""",
                (limit, offset)
            ).fetchall()
            
            total = conn.execute("SELECT COUNT(*) FROM games WHERE end_time IS NOT NULL").fetchone()[0]
        
        return jsonify({
            "games": [dict(game) for game in games],
            "total": total,
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        logger.error(f"Error fetching game history: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/game/<int:game_id>', methods=['GET'])
def get_game_details(game_id: int):
    """Get detailed information about a specific game"""
    try:
        with get_db() as conn:
            game = conn.execute(
                "SELECT * FROM games WHERE id = ?",
                (game_id,)
            ).fetchone()
            
            if not game:
                return jsonify({"error": "Game not found"}), 404
            
            moves = conn.execute(
                """SELECT move_number, move_notation, fen_after, evaluation, best_move, timestamp
                   FROM moves 
                   WHERE game_id = ? 
                   ORDER BY move_number""",
                (game_id,)
            ).fetchall()
        
        return jsonify({
            "game": dict(game),
            "moves": [dict(move) for move in moves]
        })
        
    except Exception as e:
        logger.error(f"Error fetching game details: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/analyze-position', methods=['POST'])
def analyze_position():
    """Analyze a specific position"""
    if engine is None:
        return jsonify({"error": "Engine not available"}), 503
    
    try:
        data = request.get_json()
        fen = data.get('fen')
        depth = data.get('depth', 20)
        
        if not fen:
            return jsonify({"error": "FEN required"}), 400
        
        # Create temporary board
        try:
            temp_board = chess.Board(fen)
        except ValueError:
            return jsonify({"error": "Invalid FEN"}), 400
        
        # Analyze position
        info = engine.analyse(temp_board, chess.engine.Limit(depth=depth))
        
        result = {
            "best_moves": [],  # Keep for compatibility
            "position_type": "Position",  # Generic label
            "turn": "white" if temp_board.turn else "black",
            "evaluation": 0.0  # Default evaluation
        }
        
        score = info.get('score')
        if score:
            if score.is_mate():
                # Handle mate scores
                mate_in = score.relative.mate()
                if mate_in:
                    result["evaluation"] = 100.0 if mate_in > 0 else -100.0
            else:
                # Convert centipawns to pawns (divide by 100)
                result["evaluation"] = score.relative.score(mate_score=10000) / 100.0
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error analyzing position: {e}")
        return jsonify({"error": str(e)}), 500

def get_termination_reason(board: chess.Board) -> str:
    """Get the reason for game termination"""
    if board.is_checkmate():
        return "Checkmate"
    elif board.is_stalemate():
        return "Stalemate"
    elif board.is_insufficient_material():
        return "Insufficient material"
    elif board.is_seventyfive_moves():
        return "75-move rule"
    elif board.is_fivefold_repetition():
        return "Fivefold repetition"
    elif board.can_claim_draw():
        return "Draw by repetition"
    else:
        return "Unknown"

def get_position_type(board: chess.Board) -> str:
    """Categorize the current position"""
    piece_count = len(board.piece_map())
    
    if piece_count > 24:
        return "Opening"
    elif piece_count > 10:
        return "Middlegame"
    else:
        return "Endgame"

def graceful_shutdown(signum, frame):
    """Handle graceful shutdown"""
    logger.info("Shutting down gracefully...")
    
    if engine:
        try:
            engine.quit()
            logger.info("Engine closed")
        except Exception as e:
            logger.error(f"Error closing engine: {e}")
    
    sys.exit(0)

# Initialize everything on startup
if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)
    
    # Initialize components
    init_database()
    init_engine()
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)