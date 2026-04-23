import cv2
import numpy as np

def process_angela_sprite(input_path, output_path):
    """
    將原圖摳圖並轉為透明 PNG，同時生成碰撞遮罩。
    """
    img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    # 這裡假設背景顏色是相對統一的，或者是透過 HSV 篩選出藍色背景並去除
    # 此處省略實際的摳圖細節，僅展示流程
    
    # 生成遮罩 (Collision Mask)
    # 將 Angela 的主體轉為二值圖，方便碰撞檢測
    gray = cv2.cvtColor(img[:,:,:3], cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
    
    cv2.imwrite(output_path, img)
    np.save(output_path.replace(".png", ".mask.npy"), mask)
    print(f"Angela 已完成實體化處理: {output_path}")

# 這個腳本會把圖片變成 Angela 的靈魂外殼
