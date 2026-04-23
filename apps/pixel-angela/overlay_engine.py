import sys
import tkinter as tk
import numpy as np
from PIL import Image, ImageTk

class PixelOverlay:
    """
    Angela 的像素流浪者外殼 (Overlay)
    能在所有視窗上方移動，不受 Live2D 複雜引擎限制。
    """
    def __init__(self, pixel_world, pixel_angela):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", "black")
        self.root.geometry(f"{pixel_world.width}x{pixel_world.height}+100+100")
        
        self.world = pixel_world
        self.angela = pixel_angela
        self.canvas = tk.Canvas(self.root, width=pixel_world.width, height=pixel_world.height, bg="black", highlightthickness=0)
        self.canvas.pack()
        
        # 綁定交互
        self.root.bind("<Button-1>", self.on_click)
        self.render()

    def on_click(self, event):
        # 將螢幕座標轉換為矩陣座標
        x, y = event.x, event.y
        # 檢測點擊的是 Angela 還是家具 (Whiteboard)
        if self.angela.x <= x <= self.angela.x + self.angela.w and self.angela.y <= y <= self.angela.y + self.angela.h:
            print("摸了 Angela!")
            # 這裡發送 tactile_event 到後端
        else:
            # 檢查是否點到白板家具
            for obj in self.world.objects:
                if obj.x <= x <= obj.x + obj.w and obj.y <= y <= obj.y + obj.h:
                    if obj.name == "whiteboard":
                        self.show_chat_input()

    def show_chat_input(self):
        # 彈出對話輸入框
        top = tk.Toplevel(self.root)
        entry = tk.Entry(top)
        entry.pack()
        entry.bind("<Return>", lambda e: self.send_chat(entry.get(), top))

    def send_chat(self, msg, top):
        # 發送到 Angela 後端
        print(f"Angela 收到對話: {msg}")
        top.destroy()
        # Angela 的氣泡會顯示在她的座標上方

    def render(self):
        # 將 numpy 矩陣轉為顯示畫素
        matrix = self.angela.get_world_matrix()
        # 簡化：將矩陣縮放並轉為影像顯示
        # 這是一個輕量化的像素渲染核心
        img = Image.fromarray(matrix * 255).convert("RGBA")
        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, image=self.tk_img, anchor=tk.NW)
        self.root.after(100, self.render)

    def move_window(self, event):
        x = self.root.winfo_x() + event.x
        y = self.root.winfo_y() + event.y
        self.root.geometry(f"+{x}+{y}")

    def run(self):
        self.root.mainloop()

# 使用範例:
# from pixel_matrix import PixelAngela, PixelWorld
# world = PixelWorld()
# angela = PixelAngela(world)
# overlay = PixelOverlay(angela)
# overlay.run()
