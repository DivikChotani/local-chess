import chess
import chess.engine

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

# Game loop
while not board.is_game_over():
    info = engine.analyse(board, chess.engine.Limit(time=0.1), multipv=10)
    for i, info in enumerate(info):
            move = info["pv"][0] if "pv" in info else None
            score = info["score"].white()
            print(f"#{i+1} Best move: {move}, Score: {score}")
    if board.turn == chess.WHITE:
        result = engine_white.play(board, chess.engine.Limit(time=0.1))
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