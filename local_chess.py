import chess
import chess.engine

engine = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")
board = chess.Board()

print(board)
white = True
while not board.is_game_over():
    result = engine.play(board, chess.engine.Limit(time=0.1))
    info = engine.analyse(board, chess.engine.Limit(time=0.1))
    print("White") if white==True else print("Black")
    white = not white
    print("best move:", result.move)
    print("Score:", info["score"].white())

    board.push(result.move)
    print(board)



engine.quit()
