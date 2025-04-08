import chess
import chess.engine
engine = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")
board = chess.Board()

print(board)
white = True
while not board.is_game_over():
    result = engine.play(board, chess.engine.Limit(time=0.1))
    info = engine.analyse(board, chess.engine.Limit(time=0.1), multipv=10)
    print("White") if white==True else print("Black")
    white = not white
    for i, info in enumerate(info):
        move = info["pv"][0] if "pv" in info else None
        score = info["score"].white()
        print(f"#{i+1} Best move: {move}, Score: {score}")

    board.push(result.move)
    print(board)



engine.quit()
