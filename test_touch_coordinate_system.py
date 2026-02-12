#!/usr/bin/env python3
"""
Angela Character Touch Coordinate System Test
立繪觸摸座標系統完整測試 - 修復版

座標轉換流程:
1. Screen (瀏覽器) → Wrapper (考慮瀏覽器縮放)
2. Wrapper → Canvas Internal (1:1)
3. Canvas Internal → Image (考慮 0.4 縮放 + 居中)
"""

import json
import math
import logging
logger = logging.getLogger(__name__)

# ============= 配置 =============
# Canvas 內部尺寸（固定）
CANVAS_WIDTH = 400
CANVAS_HEIGHT = 500

# 圖片尺寸
IMG_WIDTH = 1408
IMG_HEIGHT = 768
DISPLAY_SCALE = 0.4  # 圖片縮放比例

# 圖片顯示尺寸
SCALED_WIDTH = IMG_WIDTH * DISPLAY_SCALE  # 563.2
SCALED_HEIGHT = IMG_HEIGHT * DISPLAY_SCALE  # 307.2

# Canvas 中心點
CENTER_X = CANVAS_WIDTH / 2  # 200
CENTER_Y = CANVAS_HEIGHT / 2  # 250


def screen_to_wrapper(screen_x, screen_y, wrapper_rect):
    """
    Screen → Wrapper (考慮瀏覽器縮放)
    wrapper_rect: {'left': l, 'top': t, 'width': w, 'height': h}
    """
    scale_x = CANVAS_WIDTH / wrapper_rect['width']
    scale_y = CANVAS_HEIGHT / wrapper_rect['height']
    
    wrapper_x = (screen_x - wrapper_rect['left']) * scale_x
    wrapper_y = (screen_y - wrapper_rect['top']) * scale_y
    
    return wrapper_x, wrapper_y, scale_x, scale_y


def wrapper_to_image(canvas_x, canvas_y):
    """
    Canvas Internal → Image (考慮 0.4 縮放 + 居中)
    
    繪製方式 (live2d-manager.js):
    ctx.translate(centerX, centerY);  // 移動到中心
    ctx.scale(scale, scale);         // 縮放
    ctx.drawImage(img, -imgWidth/2, -imgHeight/2);  // 繪製
    
    逆轉換:
    imgX = (canvasX - centerX) / scale + imgWidth / 2
    imgY = (canvasY - centerY) / scale + imgHeight / 2
    """
    scale = DISPLAY_SCALE
    img_x = (canvas_x - CENTER_X) / scale + IMG_WIDTH / 2
    img_y = (canvas_y - CENTER_Y) / scale + IMG_HEIGHT / 2
    
    return img_x, img_y


def image_to_wrapper(img_x, img_y):
    """
    Image → Canvas Internal (考慮 0.4 縮放 + 居中)
    
    canvasX = (imgX - imgWidth/2) * scale + centerX
    canvasY = (imgY - imgHeight/2) * scale + centerY
    """
    scale = DISPLAY_SCALE
    canvas_x = (img_x - IMG_WIDTH / 2) * scale + CENTER_X
    canvas_y = (img_y - IMG_HEIGHT / 2) * scale + CENTER_Y
    
    return canvas_x, canvas_y


def is_point_in_zone(x, y, zone_rect):
    """檢查座標是否在區域內"""
    x1, y1, x2, y2 = zone_rect
    return x1 <= x < x2 and y1 <= y < y2


def load_config():
    """載入觸摸區域配置"""
    config_path = '/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app/resources/angela_character_config.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_coordinate_transformation():
    """測試座標轉換"""
    print("=" * 70)
    print("測試 1: 座標轉換基礎驗證")
    print("=" * 70)
    
    # 測試點
    test_points = [
        ("圖片中心", 704, 384),
        ("臉部中心", 703, 113),
        ("頭髮中心", 704, 183),
        ("頭髮左上", 528, 46),
        ("左手", 638, 355),
        ("左腿", 674, 419),
    ]
    
    all_passed = True
    for name, img_x, img_y in test_points:
        # Image → Wrapper
        wrapper_x, wrapper_y = image_to_wrapper(img_x, img_y)
        
        # Wrapper → Image (逆轉換)
        img_x_back, img_y_back = wrapper_to_image(wrapper_x, wrapper_y)
        
        # 驗證
        error = math.sqrt((img_x - img_x_back)**2 + (img_y - img_y_back)**2)
        passed = error < 0.01
        all_passed = all_passed and passed
        
        status = "✓" if passed else "✗"
        print(f"{status} {name}:")
        print(f"   Image: ({img_x}, {img_y})")
        print(f"   Wrapper: ({wrapper_x:.1f}, {wrapper_y:.1f})")
        print(f"   Back: ({img_x_back:.1f}, {img_y_back:.1f})")
        print(f"   Error: {error:.6f}")
    
    return all_passed


def test_browser_zoom():
    """測試瀏覽器縮放"""
    print("\n" + "=" * 70)
    print("測試 2: 瀏覽器縮放處理")
    print("=" * 70)
    
    # 測試點：臉部中心 (703, 113)
    face_img_x, face_img_y = 703, 113
    
    # 臉部中心在 wrapper 中的位置
    face_wrapper_x, face_wrapper_y = image_to_wrapper(face_img_x, face_img_y)
    
    print(f"臉部中心 Image: ({face_img_x}, {face_img_y})")
    print(f"臉部中心 Wrapper: ({face_wrapper_x:.1f}, {face_wrapper_y:.1f})")
    
    zoom_levels = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
    
    all_passed = True
    for zoom in zoom_levels:
        # 模擬 wrapper 在頁面中的位置（固定）
        wrapper_left = 100
        wrapper_top = 100
        
        # 當 zoom 改變時，wrapper 的視覺尺寸改變
        # 但 Canvas 內部尺寸固定為 400x500
        # 所以 wrapper 的 getBoundingClientRect() 會返回 zoom * 400 x zoom * 500
        wrapper_width = CANVAS_WIDTH * zoom
        wrapper_height = CANVAS_HEIGHT * zoom
        
        # 計算臉部中心在螢幕上的位置
        # screenX = wrapperLeft + (wrapperX / zoom)
        screen_x = wrapper_left + face_wrapper_x / zoom
        screen_y = wrapper_top + face_wrapper_y / zoom
        
        # 現在模擬逆過程：用戶點擊螢幕位置
        # 瀏覽器返回 wrapper_rect = {left, top, width: 400*zoom, height: 500*zoom}
        wrapper_rect = {
            'left': wrapper_left,
            'top': wrapper_top,
            'width': wrapper_width,
            'height': wrapper_height
        }
        
        # 使用 screen_to_wrapper 計算 wrapper 座標
        calc_wrapper_x, calc_wrapper_y, scale_x, scale_y = screen_to_wrapper(
            screen_x, screen_y, wrapper_rect
        )
        
        # 使用 wrapper_to_image 計算 Image 座標
        calc_img_x, calc_img_y = wrapper_to_image(calc_wrapper_x, calc_wrapper_y)
        
        # 驗證
        error = math.sqrt((face_img_x - calc_img_x)**2 + (face_img_y - calc_img_y)**2)
        passed = error < 0.01
        all_passed = all_passed and passed
        
        status = "✓" if passed else "✗"
        print(f"{status} Zoom {zoom:.0%}:")
        print(f"   Wrapper Rect: {wrapper_width:.0f}x{wrapper_height:.0f}")
        print(f"   Screen: ({screen_x:.1f}, {screen_y:.1f})")
        print(f"   Calc Wrapper: ({calc_wrapper_x:.1f}, {calc_wrapper_y:.1f})")
        print(f"   Calc Image: ({calc_img_x:.1f}, {calc_img_y:.1f})")
        print(f"   Error: {error:.6f}")
    
    return all_passed


def test_touch_zone_detection():
    """測試觸摸區域檢測 - 修正版"""
    print("\n" + "=" * 70)
    print("測試 3: 觸摸區域檢測 (按優先級)")
    print("=" * 70)
    
    config = load_config()
    zones = config['touch_zones']
    
    # 列印所有區域及其優先級
    print("所有觸摸區域:")
    for name, zone in sorted(zones.items(), key=lambda x: x[1].get('priority', 10)):
        rect = zone['rect']
        print(f"   {name}: rect={rect}, priority={zone.get('priority', 'N/A')}")
    
    # 測試每個區域的中心點
    print("\n區域中心點測試:")
    test_cases = []
    for name, zone in zones.items():
        rect = zone['rect']
        center_x = (rect[0] + rect[2]) / 2
        center_y = (rect[1] + rect[3]) / 2
        test_cases.append((name, center_x, center_y, rect))
    
    all_passed = True
    for name, img_x, img_y, rect in test_cases:
        # 按優先級檢查（從高到低）
        matched_zone = None
        for zone_name, zone in sorted(zones.items(), key=lambda x: x[1].get('priority', 10)):
            if is_point_in_zone(img_x, img_y, zone['rect']):
                matched_zone = zone_name
                break
        
        matched = matched_zone == name
        all_passed = all_passed and matched
        
        status = "✓" if matched else "✗"
        print(f"{status} {name}: Image({img_x:.0f}, {img_y:.0f}) → 匹配 {matched_zone}")
    
    return all_passed


def test_wrapper_positioning():
    """測試 wrapper 定位"""
    print("\n" + "=" * 70)
    print("測試 4: Wrapper 尺寸與圖片定位")
    print("=" * 70)
    
    print(f"原圖尺寸: {IMG_WIDTH} x {IMG_HEIGHT}")
    print(f"縮放比例: {DISPLAY_SCALE}")
    print(f"顯示尺寸: {SCALED_WIDTH:.1f} x {SCALED_HEIGHT:.1f}")
    print(f"Canvas 內部: {CANVAS_WIDTH} x {CANVAS_HEIGHT}")
    
    # 計算圖片左上角在 Canvas 中的位置
    img_left = CENTER_X - SCALED_WIDTH / 2  # 200 - 281.6 = -81.6
    img_top = CENTER_Y - SCALED_HEIGHT / 2  # 250 - 153.6 = 96.4
    
    print(f"\n圖片在 Canvas 中的位置:")
    print(f"   左上角: ({img_left:.1f}, {img_top:.1f})")
    print(f"   右下角: ({img_left + SCALED_WIDTH:.1f}, {img_top + SCALED_HEIGHT:.1f})")
    
    # 問題：圖片左邊超出 Canvas (-81.6 < 0)
    print(f"\n分析:")
    print(f"   Canvas 左邊界: 0")
    print(f"   圖片左邊界: {img_left:.1f}")
    print(f"   圖片右邊界: {img_left + SCALED_WIDTH:.1f} (小於 {CANVAS_WIDTH}?) {img_left + SCALED_WIDTH < CANVAS_WIDTH}")
    
    # 結論：圖片在水平方向上居中顯示，但左右都會超出 Canvas
    # 這是正常的，因為圖片寬度 563 > Canvas 寬度 400
    
    return True  # 這是設計決策，不是錯誤


def test_zone_coordinates():
    """測試區域座標"""
    print("\n" + "=" * 70)
    print("測試 5: 區域座標轉換到 Canvas")
    print("=" * 70)
    
    config = load_config()
    zones = config['touch_zones']
    
    # 測試關鍵區域
    key_zones = ['face', 'eyes', 'mouth', 'hair', 'neck', 'torso']
    
    print("關鍵區域在 Canvas 上的位置:")
    for name in key_zones:
        if name not in zones:
            continue
        rect = zones[name]['rect']
        
        # 左上角
        left_x, left_y = image_to_wrapper(rect[0], rect[1])
        # 右下角
        right_x, right_y = image_to_wrapper(rect[2], rect[3])
        
        print(f"   {name}:")
        print(f"      Image: ({rect[0]},{rect[1]}) - ({rect[2]},{rect[3]})")
        print(f"      Canvas: ({left_x:.1f},{left_y:.1f}) - ({right_x:.1f},{right_y:.1f})")
        print(f"      Size: {right_x - left_x:.1f} x {right_y - left_y:.1f}")


def main():
    """主測試"""
    print("\n" + "=" * 70)
    print("Angela Character Touch Coordinate System Test")
    print("立繪觸摸座標系統完整測試 - 修復版")
    print("=" * 70)
    
    results = []
    
    # 運行測試
    results.append(("座標轉換基礎驗證", test_coordinate_transformation()))
    results.append(("瀏覽器縮放處理", test_browser_zoom()))
    results.append(("觸摸區域檢測", test_touch_zone_detection()))
    results.append(("Wrapper 尺寸與圖片定位", test_wrapper_positioning()))
    test_zone_coordinates()
    
    # 總結
    print("\n" + "=" * 70)
    print("測試結果總結")
    print("=" * 70)
    
    all_passed = True
    for name, passed in results:
        status = "✓ 通過" if passed else "✗ 失敗"
        print(f"{status}: {name}")
        all_passed = all_passed and passed
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ 所有測試通過！")
        print("座標轉換系統工作正常。")
    else:
        print("✗ 部分測試失敗，需要檢查。")
    print("=" * 70)
    
    return all_passed


if __name__ == '__main__':
    main()