from PyQt6.QtGui import QColor, QFont

class UIConfig:
    # 全局比例
    ANGELA_WIDTH = 128
    ANGELA_HEIGHT = 384
    BUBBLE_CORNER_RADIUS = 12
    BUBBLE_PADDING = 12
    
    # 性能優化
    RENDER_INTERVAL = 100 # 降低到 10 FPS 以節省 CPU
    WS_RECONNECT_DELAY = 5.0

    # Angela (Output) 樣式
    ANGELA_BUBBLE_BG = QColor(255, 255, 255) # 純白
    ANGELA_TEXT_COLOR = QColor(0, 0, 0)      # 黑字
    ANGELA_FONT_WEIGHT = QFont.Weight.Normal
    ANGELA_UNDERLINE = False

    # User (Input) 樣式
    USER_BUBBLE_BG = QColor(240, 245, 255)   # 淺藍灰
    USER_TEXT_COLOR = QColor(0, 0, 0)        # 黑字
    USER_FONT_WEIGHT = QFont.Weight.Bold     # 粗體
    USER_UNDERLINE = True                    # 下劃線
