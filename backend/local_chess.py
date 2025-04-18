from flask import Flask, request, jsonify
import chess
import chess.engine
import chess.svg
import sqlite3

engine = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")

conn = sqlite3.connect("chess-games.db")

cursor = conn.cursor()

# Start two Stockfish instances
# engine_white = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")
# engine_black = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")
# engine_white.configure({
#     "UCI_LimitStrength": True,
#     "UCI_Elo": 2500  # You can set 1350, 1600, etc. too
# })
# # Set weaker ELO for Black
# engine_black.configure({
#     "UCI_LimitStrength": True,
#     "UCI_Elo": 1320  # You can set 1350, 1600, etc. too
# })

board = chess.Board()
# print("Starting position:")
# print(board)
# print(board.fen())

app = Flask(__name__)
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
            
            
# while not board.is_game_over():
#     info = engine.analyse(board, chess.engine.Limit(time=0.1), multipv=10)
#     for i, info in enumerate(info):
#             move = info["pv"][0] if "pv" in info else None
#             score = info["score"].white()
#             print(f"#{i+1} Best move: {move}, Score: {score}")
#     if board.turn == chess.WHITE:
#         result = engine_white.play(board, chess.engine.Limit(time=0.1))
#         print(result)

#         print("White (Strong) plays:", result.move)
#     else:
#         result = engine_black.play(board, chess.engine.Limit(time=0.1))
#         print("Black (Weak) plays:", result.move)
#     board.push(result.move)
#     print(board)

# # Show result
# print("Game over:", board.result())

# Clean up
conn.commit()
conn.close()

# engine_white.quit()
# engine_black.quit()
engine.quit()