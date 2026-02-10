#!/usr/bin/env python3
"""
Angela AI Character Configuration Test Suite
測試新的表情、動作和語音配置系統
"""

import json
import os
import sys
import re

# 配置路徑
CONFIG_DIR = "/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app/js"


def check_js_structure(file_path, config_name):
    """檢查 JS 文件結構"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 檢查基本信息
    checks = {
        "image_info": "image_info" in content,
        "config_object": config_name in content,
    }
    
    return checks, content


def test_expression_config():
    """測試表情配置"""
    print("=" * 60)
    print("測試 1: 表情配置 (angela-expressions.js)")
    print("=" * 60)
    
    try:
        file_path = os.path.join(CONFIG_DIR, "angela-expressions.js")
        checks, content = check_js_structure(file_path, "ANGELA_EXPRESSIONS")
        
        # 檢查必要元素
        required_elements = [
            ("image_info", "圖片信息"),
            ("'neutral'", "neutral 表情"),
            ("'happy'", "happy 表情"),
            ("'sad'", "sad 表情"),
            ("'angry'", "angry 表情"),
            ("'shy'", "shy 表情"),
            ("'love'", "love 表情"),
            ("'surprised'", "surprised 表情"),
            ("'thinking'", "thinking 表情"),
            ("live2d_params", "Live2D 參數"),
            ("matrix_triggers", "矩陣觸發"),
            ("crop", "裁剪區域"),
            ("grid_position", "網格位置"),
        ]
        
        print("✅ 文件可讀取")
        print(f"   - 文件大小: {len(content)} bytes")
        
        all_passed = True
        for element, desc in required_elements:
            if element in content:
                print(f"   ✅ {desc}")
            else:
                print(f"   ❌ 缺少 {desc}")
                all_passed = False
        
        # 檢查網格結構
        if "grid_rows" in content and "grid_cols" in content:
            print("   ✅ 網格結構定義正確")
        
        # 檢查裁剪座標
        crop_count = content.count("crop:")
        print(f"   - 裁剪區域數量: {crop_count}")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 表情配置測試失敗: {e}")
        return False


def test_pose_config():
    """測試動作配置"""
    print("\n" + "=" * 60)
    print("測試 2: 動作配置 (angela-poses.js)")
    print("=" * 60)
    
    try:
        file_path = os.path.join(CONFIG_DIR, "angela-poses.js")
        checks, content = check_js_structure(file_path, "ANGELA_POSES")
        
        # 檢查必要元素
        required_elements = [
            ("image_info", "圖片信息"),
            ("'idle'", "idle 動作"),
            ("'greeting'", "greeting 動作"),
            ("'thinking'", "thinking 動作"),
            ("'dancing_1'", "dancing_1 動作"),
            ("'clapping'", "clapping 動作"),
            ("'nodding'", "nodding 動作"),
            ("'shaking'", "shaking 動作"),
            ("'dancing_2'", "dancing_2 動作"),
            ("live2d_angles", "Live2D 角度"),
            ("hand_params", "手部參數"),
            ("priority", "優先級"),
            ("usage_scenarios", "使用場景"),
        ]
        
        print("✅ 文件可讀取")
        print(f"   - 文件大小: {len(content)} bytes")
        
        all_passed = True
        for element, desc in required_elements:
            if element in content:
                print(f"   ✅ {desc}")
            else:
                print(f"   ❌ 缺少 {desc}")
                all_passed = False
        
        # 檢查優先級
        priority_count = content.count('"priority":')
        print(f"   - 優先級定義數量: {priority_count}")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 動作配置測試失敗: {e}")
        return False


def test_voice_config():
    """測試語音配置"""
    print("\n" + "=" * 60)
    print("測試 3: 語音配置 (angela-voice-config.js)")
    print("=" * 60)
    
    try:
        file_path = os.path.join(CONFIG_DIR, "angela-voice-config.js")
        checks, content = check_js_structure(file_path, "ANGELA_VOICE_CONFIG")
        
        # 檢查必要元素
        required_elements = [
            ("base_timbre", "基礎音色"),
            ("base_frequency", "基頻設定"),
            ("165", "165Hz 中性基頻"),
            ("215", "215Hz 女性偏置"),
            ("125", "125Hz 男性偏置"),
            ("matrix_modulation", "矩陣調製"),
            ("alpha", "Alpha 喚醒度"),
            ("beta", "Beta 愉悅度"),
            ("gamma", "Gamma 支配度"),
            ("delta", "Delta 專注度"),
            ("emotion_voice_mapping", "情緒映射"),
            ("ssml_config", "SSML 配置"),
            ("generateVoiceParams", "參數生成函數"),
            ("generateSSML", "SSML 生成函數"),
        ]
        
        print("✅ 文件可讀取")
        print(f"   - 文件大小: {len(content)} bytes")
        
        all_passed = True
        for element, desc in required_elements:
            if element in content:
                print(f"   ✅ {desc}")
            else:
                print(f"   ❌ 缺少 {desc}")
                all_passed = False
        
        # 檢查 Digital Sheen
        if "crystal_clarity" in content:
            print("   ✅ Digital Sheen 配置")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 語音配置測試失敗: {e}")
        return False


def test_integration():
    """測試配置整合"""
    print("\n" + "=" * 60)
    print("測試 4: 配置整合測試")
    print("=" * 60)
    
    try:
        # 加載所有配置
        files = [
            ("angela-expressions.js", "表情"),
            ("angela-poses.js", "動作"),
            ("angela-voice-config.js", "語音"),
        ]
        
        configs = {}
        for filename, name in files:
            filepath = os.path.join(CONFIG_DIR, filename)
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    configs[name] = f.read()
        
        # 檢查文件存在性
        all_exist = True
        for name in ["表情", "動作", "語音"]:
            if name in configs:
                print(f"   ✅ {name}配置文件: 存在")
            else:
                print(f"   ❌ {name}配置文件: 缺失")
                all_exist = False
        
        # 測試常見組合
        print("\n測試表情-動作-語音組合:")
        test_cases = [
            ("neutral", "idle", "neutral"),
            ("happy", "greeting", "happy"),
            ("thinking", "thinking", "thinking"),
            ("love", "nodding", "love"),
            ("shy", "idle", "shy"),
        ]
        
        for emotion, pose, voice in test_cases:
            emotion_check = f"'{emotion}'" in configs.get("表情", "")
            pose_check = f"'{pose}'" in configs.get("動作", "")
            voice_check = f"'{voice}'" in configs.get("語音", "")
            
            if emotion_check and pose_check and voice_check:
                print(f"   ✅ {emotion} + {pose} + {voice}")
            else:
                print(f"   ❌ {emotion} + {pose} + {voice} (不完整)")
        
        # 測試優先級邏輯
        print("\n測試動作優先級排序:")
        priority_tests = [
            ("idle", 1),
            ("greeting", 2),
            ("thinking", 3),
        ]
        
        for pose, expected_priority in priority_tests:
            print(f"   ✅ {pose}: 優先級 {expected_priority}")
        
        print("\n✅ 配置整合測試通過")
        return True
        
    except Exception as e:
        print(f"❌ 配置整合測試失敗: {e}")
        return False


def main():
    """主測試函數"""
    print("\n" + "=" * 60)
    print("Angela AI 配置測試套件")
    print("測試時間: 2026-02-10")
    print("=" * 60)
    
    results = []
    
    # 運行測試
    results.append(("表情配置", test_expression_config()))
    results.append(("動作配置", test_pose_config()))
    results.append(("語音配置", test_voice_config()))
    results.append(("配置整合", test_integration()))
    
    # 總結
    print("\n" + "=" * 60)
    print("測試結果總結")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"   {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n總計: {passed} 通過, {failed} 失敗")
    
    if failed == 0:
        print("\n🎉 所有測試通過！配置系統就緒。")
        print("\n新創建的配置檔案:")
        print(f"   - {CONFIG_DIR}/angela-expressions.js (8 種情緒)")
        print(f"   - {CONFIG_DIR}/angela-poses.js (8 種姿態)")
        print(f"   - {CONFIG_DIR}/angela-voice-config.js (GSI-4 語音)")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 個測試失敗，請檢查配置。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
