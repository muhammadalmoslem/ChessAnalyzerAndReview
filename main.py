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
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Chess Game Analyzer & Review")

# إعداد الخطوط
font_piece = pygame.font.SysFont("Segoe UI Symbol", 36, bold=True)
font_info = pygame.font.SysFont("Arial", 22)
font_accuracy = pygame.font.SysFont("Arial", 24, bold=True)
clock = pygame.time.Clock()

# ألوان الرقعة والواجهة
COLOR_LIGHT = (240, 217, 181)
COLOR_DARK = (181, 136, 99)
COLOR_BG_INFO = (50, 50, 50)
COLOR_TEXT = (255, 255, 255)

# ألوان تقييم النقلات
COLOR_BRILLIANT = (27, 171, 142)  # تركوازي
COLOR_BEST = (142, 190, 89)       # أخضر غامق
COLOR_GOOD = (156, 172, 181)      # رمادي/أزرق فاتح
COLOR_BOOK = (165, 117, 83)       # بني كتاب القواعد
COLOR_MISTAKE = (247, 183, 51)    # برتقالي/أصفر
COLOR_BLUNDER = (186, 54, 43)     # أحمر ناصع

PIECE_SYMBOLS = {
    "K": "♔", "Q": "♕", "R": "♖", "B": "♗", "N": "♘", "P": "♙",
    "k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟"
}

def get_move_classification(score_before, score_after, is_best_move, played_move, board_before):
    """تصنيف النقلة بناءً على الفارق في التقييم قبل وبعد الحركة وحسب لون اللاعب"""
    if board_before.fullmove_number <= 2:
        return "Book", COLOR_BOOK

    # حساب خسارة التقييم الدقيقة بناءً على من قام باللعب
    if board_before.turn == chess.WHITE:
        loss = score_before - score_after
    else:
        loss = score_after - score_before

    # التحقق من الكوارث (البلندر) أولاً حتى لو اعتقد المحرك خطأً بوجود تداخل
    if loss >= 1.3:
        return "Blunder !!", COLOR_BLUNDER
    elif loss >= 0.6:
        return "Mistake !", COLOR_MISTAKE
    elif loss >= 0.2:
        return "Good", COLOR_GOOD

    if is_best_move:
        # تضحية تكتيكية ناجحة ترفع التقييم
        if board_before.is_capture(played_move) and loss < -0.4:
            return "Brilliant !!", COLOR_BRILLIANT
        return "Best Move", COLOR_BEST
        
    return "Excellent", COLOR_BEST

def draw_board(screen):
    for row in range(8):
        for col in range(8):
            color = COLOR_LIGHT if (row + col) % 2 == 0 else COLOR_DARK
            pygame.draw.rect(screen, color, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def draw_pieces(screen, board):
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            symbol = piece.symbol()
            unicode_char = PIECE_SYMBOLS.get(symbol, symbol)
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
            text_color = (255, 255, 255) if symbol.isupper() else (0, 0, 0)
            p_surface = font_piece.render(unicode_char, True, text_color)
            p_rect = p_surface.get_rect(center=(col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2))
            screen.blit(p_surface, p_rect)

def draw_info(screen, move_num, turn, played, best, score, classification, class_color):
    pygame.draw.rect(screen, COLOR_BG_INFO, pygame.Rect(BOARD_SIZE, 0, INFO_WIDTH, WINDOW_HEIGHT))
    
    texts = [
        f"Move: {move_num} ({turn})",
        f"Played Move: {played}",
        f"Best Move: {best}",
        f"Engine Score: {score}",
    ]
    
    y_offset = 40
    for text in texts:
        txt_surface = font_info.render(text, True, COLOR_TEXT)
        screen.blit(txt_surface, (BOARD_SIZE + 20, y_offset))
        y_offset += 40
    
    y_offset += 10
    lbl_surface = font_info.render("Rating: ", True, COLOR_TEXT)
    screen.blit(lbl_surface, (BOARD_SIZE + 20, y_offset))
    
    class_surface = font_accuracy.render(classification, True, class_color)
    screen.blit(class_surface, (BOARD_SIZE + 90, y_offset))
    
    y_offset += 80
    help_texts = [
        "Press [SPACE] for Next Move",
        "Press [ESC] to Quit"
    ]
    for text in help_texts:
        txt_surface = font_info.render(text, True, (180, 180, 180))
        screen.blit(txt_surface, (BOARD_SIZE + 20, y_offset))
        y_offset += 35

# المتغيرات الأساسية
move_index = 0
current_move_info = {
    "num": 1, "turn": "White", "played": "None", "best": "None", 
    "score": "0.0", "class": "None", "color": COLOR_TEXT
}

running = True
while running:
    screen.fill((0, 0, 0))
    
    draw_board(screen)
    draw_pieces(screen, board)
    draw_info(screen, current_move_info["num"], current_move_info["turn"], 
              current_move_info["played"], current_move_info["best"], 
              current_move_info["score"], current_move_info["class"], current_move_info["color"])
    
    pygame.display.flip()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
                
            elif event.key == pygame.K_SPACE and move_index < len(moves_list):
                move = moves_list[move_index]
                
                board_before = board.copy()
                current_move_info["num"] = board.fullmove_number
                current_move_info["turn"] = "White" if board.turn == chess.WHITE else "Black"
                
                # 1. تحليل الموقف قبل الحركة لعمق مناسب
                pre_analysis = engine.analyse(board, chess.engine.Limit(depth=14))
                pv_line = pre_analysis.get("pv", [])
                
                # تعديل جوهري: استخراج النقلة الأولى المقترحة فقط بدقة للمقارنة العادلة
                best_move_uci = pv_line[0] if pv_line else None
                
                score_obj_before = pre_analysis["score"].white()
                if score_obj_before.is_mate():
                    score_before_numeric = 15.0 if score_obj_before.mate() > 0 else -15.0
                else:
                    score_before_numeric = (score_obj_before.score() or 0) / 100.0
                
                # المقارنة الصحيحة الآن تتم بين كائني النقلة مباشرة
                is_best_move = (move == best_move_uci)
                current_move_info["best"] = board.san(best_move_uci) if best_move_uci else "None"
                current_move_info["played"] = board.san(move)
                
                # 2. تنفيذ الحركة
                board.push(move)
                
                # 3. تحليل الموقف بعد الحركة
                if board.is_checkmate():
                    current_move_info["score"] = "#"
                    current_move_info["class"] = "Best Move" if is_best_move else "Blunder !!"
                    current_move_info["color"] = COLOR_BEST if is_best_move else COLOR_BLUNDER
                else:
                    post_analysis = engine.analyse(board, chess.engine.Limit(depth=14))
                    score_obj_after = post_analysis["score"].white()
                    
                    if score_obj_after.is_mate():
                        mate = score_obj_after.mate()
                        current_move_info["score"] = f"#{mate}" if mate > 0 else f"-#{abs(mate)}"
                        score_after_numeric = 15.0 if mate > 0 else -15.0
                    else:
                        score_after_numeric = (score_obj_after.score() or 0) / 100.0
                        current_move_info["score"] = str(score_after_numeric)
                    
                    # حساب وتحديث التصنيف بعد معالجة الأخطاء
                    cls_name, cls_color = get_move_classification(
                        score_before_numeric, score_after_numeric, is_best_move, move, board_before
                    )
                    current_move_info["class"] = cls_name
                    current_move_info["color"] = cls_color
                
                move_index += 1

    clock.tick(30)

engine.quit()
pygame.quit()
sys.exit()
