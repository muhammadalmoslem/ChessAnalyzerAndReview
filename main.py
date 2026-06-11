import chess
import chess.pgn
import chess.engine

engine = chess.engine.SimpleEngine.popen_uci(
    r"C:\Users\foxno\Downloads\stockfish-windows-x86-64-avx2 (1)\stockfish\stockfish-windows-x86-64-avx2.exe"
)

with open(r"C:\Users\foxno\ChessAnalyzerAndReview\game.pgn") as pgn:
    game = chess.pgn.read_game(pgn)

board = game.board()

move_number = 1

for move in game.mainline_moves():
    analysis = engine.analyse(board, chess.engine.Limit(depth=12))

    score = analysis["score"].white().score()
    best_move = analysis["pv"][0]

    print(f"Move {move_number}")
    print(f"Played: {move}")
    print(f"Best:   {best_move}")
    print(f"Score:  {score}")
    print("-" * 30)

    board.push(move)
    move_number += 1

engine.quit()