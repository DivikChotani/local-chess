from flask import Flask, request, jsonify
import chess
import chess.engine
import chess.svg

engine = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")

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
print("Starting position:")
print(board)
print(board.fen())

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
while not board.is_game_over():
    info = engine.analyse(board, chess.engine.Limit(time=0.1), multipv=10)
    for i, info in enumerate(info):
            move = info["pv"][0] if "pv" in info else None
            score = info["score"].white()
            print(f"#{i+1} Best move: {move}, Score: {score}")
    if board.turn == chess.WHITE:
        result = engine_white.play(board, chess.engine.Limit(time=0.1))
        print(result)

        print("White (Strong) plays:", result.move)
    else:
        result = engine_black.play(board, chess.engine.Limit(time=0.1))
        print("Black (Weak) plays:", result.move)
    board.push(result.move)
    print(board)

# Show result
print("Game over:", board.result())

# Clean up
engine_white.quit()
engine_black.quit()
engine.quit()