import sys
import chess
import chess.engine
import chess.pgn
import pygame

# --- الإعدادات والمسارات ---
STOCKFISH_PATH = r"C:\Users\foxno\Downloads\stockfish-windows-x86-64-avx2 (1)\stockfish\stockfish-windows-x86-64-avx2.exe"
PGN_PATH = r"C:\Users\foxno\ChessAnalyzerAndReview\game.pgn"

# أبعاد النافذة ورقعة الشطرنج
BOARD_SIZE = 600
SQUARE_SIZE = BOARD_SIZE // 8
INFO_WIDTH = 300
WINDOW_WIDTH = BOARD_SIZE + INFO_WIDTH
WINDOW_HEIGHT = BOARD_SIZE

# --- تشغيل محرك الشطرنج وقراءة المباراة ---
engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
with open(PGN_PATH, encoding="utf-8") as pgn:
    game = chess.pgn.read_game(pgn)

if game is None:
    print("Invalid PGN")
    engine.quit()
    exit()

moves_list = list(game.mainline_moves())
board = game.board()

# --- إعداد نافذة Pygame ---
pygame.init()
# تم تصحيح هذا السطر لتجنب الأخطاء البرمجية
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Chess Game Analyzer & Review")

# إعداد الخطوط للقطع والنصوص
font_piece = pygame.font.SysFont("Segoe UI Symbol", 36, bold=True)
font_info = pygame.font.SysFont("Arial", 22)
clock = pygame.time.Clock()

# ألوان الرقعة والواجهة
COLOR_LIGHT = (240, 217, 181)
COLOR_DARK = (181, 136, 99)
COLOR_BG_INFO = (50, 50, 50)
COLOR_TEXT = (255, 255, 255)

# قاموس لتحويل الحروف العادية إلى رموز شطرنج حقيقية وجميلة
PIECE_SYMBOLS = {
    "K": "♔", "Q": "♕", "R": "♖", "B": "♗", "N": "♘", "P": "♙",
    "k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟"
}

def draw_board(screen):
    """رسم مربعات رقعة الشطرنج"""
    for row in range(8):
        for col in range(8):
            color = COLOR_LIGHT if (row + col) % 2 == 0 else COLOR_DARK
            pygame.draw.rect(screen, color, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def draw_pieces(screen, board):
    """رسم القطع برمجياً كرموز متناسقة بدون صور خارجية"""
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            symbol = piece.symbol()
            unicode_char = PIECE_SYMBOLS.get(symbol, symbol)
            
            # تحديد الإحداثيات (قلب الصفوف لأن بايثون تبدأ من الأسفل)
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
            
            # تحديد لون النص الخلفي للقطعة لتبدو واضحة
            text_color = (255, 255, 255) if symbol.isupper() else (0, 0, 0)
            
            # رسم رمز القطعة في منتصف المربع تماماً
            p_surface = font_piece.render(unicode_char, True, text_color)
            p_rect = p_surface.get_rect(center=(col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2))
            screen.blit(p_surface, p_rect)

def draw_info(screen, move_num, turn, played, best, score):
    """رسم لوحة جانبية نصية تعرض معلومات النقلة والتحليل الحالي"""
    pygame.draw.rect(screen, COLOR_BG_INFO, pygame.Rect(BOARD_SIZE, 0, INFO_WIDTH, WINDOW_HEIGHT))
    
    texts = [
        f"Move: {move_num} ({turn})",
        f"Played Move: {played}",
        f"Best Move: {best}",
        f"Engine Score: {score}",
        "",
        "Press [SPACE] for Next Move",
        "Press [ESC] to Quit"
    ]
    
    y_offset = 40
    for text in texts:
        txt_surface = font_info.render(text, True, COLOR_TEXT)
        screen.blit(txt_surface, (BOARD_SIZE + 20, y_offset))
        y_offset += 40

# المتغيرات الأساسية للتحكم بالخطوات داخل الواجهة
move_index = 0
current_move_info = {"num": 1, "turn": "White", "played": "None", "best": "None", "score": "0.0"}

running = True
while running:
    screen.fill((0, 0, 0))
    
    # رسم عناصر اللعبة
    draw_board(screen)
    draw_pieces(screen, board)
    draw_info(screen, current_move_info["num"], current_move_info["turn"], 
              current_move_info["played"], current_move_info["best"], current_move_info["score"])
    
    pygame.display.flip()
    
    # مراقبة أزرار التحكم
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
                
            elif event.key == pygame.K_SPACE and move_index < len(moves_list):
                move = moves_list[move_index]
                
                current_move_info["num"] = board.fullmove_number
                current_move_info["turn"] = "White" if board.turn == chess.WHITE else "Black"
                
                # 1. حساب النقلة الأفضل قبل اللعب
                pre_analysis = engine.analyse(board, chess.engine.Limit(depth=15))
                pv_line = pre_analysis.get("pv", [])
                best_move_uci = pv_line[0] if pv_line else None
                current_move_info["best"] = board.san(best_move_uci) if best_move_uci else "None"
                current_move_info["played"] = board.san(move)
                
                # 2. لعب النقلة
                board.push(move)
                
                # 3. حساب التقييم بعد لعب النقلة
                if board.is_checkmate():
                    current_move_info["score"] = "#"
                else:
                    post_analysis = engine.analyse(board, chess.engine.Limit(depth=15))
                    score_obj = post_analysis["score"].white()
                    if score_obj.is_mate():
                        mate = score_obj.mate()
                        current_move_info["score"] = f"#{mate}" if mate > 0 else f"-#{abs(mate)}"
                    else:
                        current_move_info["score"] = str(score_obj.score() / 100.0)
                
                move_index += 1

    clock.tick(30)

engine.quit()
pygame.quit()
sys.exit()
