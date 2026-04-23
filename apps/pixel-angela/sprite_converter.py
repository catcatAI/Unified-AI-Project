import cv2
import numpy as np
from PIL import Image

class SpriteConverter:
    """
    將圖片轉化為 Angela DNA 矩陣
    """
    def convert(self, image_path):
        # 讀取影像
        img = cv2.imread(image_path)
        if img is None: raise ValueError("無法讀取圖片")

        # GrabCut 摳圖 (去背)
        mask = np.zeros(img.shape[:2], np.uint8)
        bgdModel = np.zeros((1, 65), np.float64)
        fgdModel = np.zeros((1, 65), np.float64)
        
        # 假設 Angela 大致在畫面中心
        rect = (10, 10, img.shape[1]-20, img.shape[0]-20)
        cv2.grabCut(img, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
        mask2 = np.where((mask==2)|(mask==0), 0, 1).astype('uint8')
        img = img * mask2[:,:,np.newaxis]

        # 縮放至 128x384
        img_resized = cv2.resize(img, (128, 384))
        
        # 轉化為我們的 DNA 矩陣 (簡單版色彩量化)
        dna_matrix = np.zeros((384, 128), dtype=np.uint8)
        # 此處僅作為示範：將影像灰度映射到我們的圖層
        gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)
        dna_matrix = (gray > 50).astype(np.uint8) * 1 # 1為皮膚/主體
        
        return dna_matrix

if __name__ == "__main__":
    converter = SpriteConverter()
    # Correct path to root directory
    dna = converter.convert(r"D:\Projects\Unified-AI-Project\angela_01.jpg")
    np.save("angela_dna_v1.npy", dna)
    print("Angela 已完成像素化轉換。")
