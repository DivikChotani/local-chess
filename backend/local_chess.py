from flask import Flask, request, jsonify
import chess
import chess.engine
import chess.svg
import sqlite3
from flask_cors import CORS
import signal
import sys



engine = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")

conn = sqlite3.connect("chess-games.db")

cursor = conn.cursor()

# Start two Stockfish instances
engine_white = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")
engine_black = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")
engine_white.configure({
    "UCI_LimitStrength": True,
    "UCI_Elo": 2500  # You can set 1350, 1600, etc. too
})
# Set weaker ELO for Black
engine_black.configure({
    "UCI_LimitStrength": True,
    "UCI_Elo": 1320  # You can set 1350, 1600, etc. too
})

board = chess.Board()
# print("Starting position:")
# print(board)
# print(board.fen())

app = Flask(__name__)
CORS(app) 


@app.post('/initialize-board')
def initializeBorad():
    return jsonify({"fen": board.fen()})

@app.post('/post-move')
def updateBoard():
    data = request.get_json()
    
    newMove = data['new-move']
    
    try:
        move = chess.Move.from_uci(newMove)
        if move not in board.legal_moves:
            return jsonify({"error":"illegal mmove"}), 400
        board.push(move)
        if board.is_game_over():
            return jsonify({
                "fen": board.fen(),
                "game_over": True,
                "result": board.result()
            })
        return jsonify({"fen":board.fen(), "game_over": False})
    except Exception as e:
        return jsonify({ "error" : str(e)}), 400
    
# Game loop
@app.post('/engine-move')
def playEngineMove():
    data = request.get_json()
    
    elo = data['elo']
    engineStrength = data['time']
    time = float(engineStrength)
    try:
        engine_white.configure({
            "UCI_LimitStrength": True,
            "UCI_Elo": elo  # You can set 1350, 1600, etc. too
        })
        result = engine_white.play(board, chess.engine.Limit(time=time))
        board.push(result.move)
        if board.is_game_over():
            return jsonify({
                "fen": board.fen(),
                "game_over": True,
                "result": board.result()
            })
        return jsonify({"fen":board.fen(), "game_over": False})
    except Exception as e:
        return jsonify({ "error" : str(e)}), 400

    
@app.get('/best-moves')
def getBestMoves():
    info = engine.analyse(board, chess.engine.Limit(time=0.1), multipv=10)
    result = []
    for t in info:
        move = t['pv'][0] if 'pv' in t else None
        score = t["score"].white()
        realScore = 0
        if score.is_mate() ==False:
            realScore = score.score()
        else: 
            realScore = score.mate()
        result.append({"move": move.uci() if move else None, 
                       "score": realScore,
                       "mate": score.is_mate()})
    try:
        return jsonify({"best moves": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
    
def graceful_shutdown(signal_received, frame):
    print('Ctrl-C detected! Cleaning up...')
    try:
        conn.commit()
        conn.close()
    except Exception as e:
        print('Error closing DB:', e)
    try:
        engine.quit()
        engine_white.quit()
        engine_black.quit()
    except Exception as e:
        print('Error quitting engines:', e)
    sys.exit(0)

# Attach signal handler
signal.signal(signal.SIGINT, graceful_shutdown)