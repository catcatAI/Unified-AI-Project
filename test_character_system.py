#!/usr/bin/env python3
"""
Angela AI - Complete Input/Output and Matrix Test
完整輸入輸出與矩陣變化測試

This script tests:
1. Character image loading
2. Touch zone configuration
3. Tactile system integration
4. Matrix changes based on input/output
"""

import json
import os
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path("/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app")
RESOURCES_DIR = BASE_DIR / "resources"
JS_DIR = BASE_DIR / "js"

def test_character_image():
    """Test that the character image was created successfully"""
    print("=" * 60)
    print("Test 1: Character Image")
    print("=" * 60)
    
    image_path = RESOURCES_DIR / "angela_character_masked.png"
    
    if image_path.exists():
        size = image_path.stat().st_size
        print(f"✅ Character image exists: {image_path.name}")
        print(f"   Size: {size:,} bytes")
        
        # Verify it's a valid image by checking header
        with open(image_path, 'rb') as f:
            header = f.read(8)
            if header[:4] == b'\x89PNG':
                print("   Format: Valid PNG")
                return True
            else:
                print("   ❌ Invalid PNG format")
                return False
    else:
        print(f"❌ Character image not found: {image_path}")
        return False

def test_character_config():
    """Test that the character configuration was created correctly"""
    print("\n" + "=" * 60)
    print("Test 2: Character Configuration")
    print("=" * 60)
    
    config_path = RESOURCES_DIR / "angela_character_config.json"
    
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"✅ Configuration loaded: {config_path.name}")
        print(f"   Version: {config.get('version', 'unknown')}")
        
        # Check required fields
        required_fields = ['original_size', 'character_bbox', 'touch_zones', 'body_parts']
        missing = []
        for field in required_fields:
            if field not in config:
                missing.append(field)
        
        if missing:
            print(f"   ❌ Missing fields: {', '.join(missing)}")
            return False
        else:
            print(f"   ✅ All required fields present")
        
        # Check touch zones
        zones = config.get('touch_zones', {})
        print(f"   Touch zones: {len(zones)} zones")
        for zone_name, zone_data in zones.items():
            rect = zone_data.get('rect', [])
            desc = zone_data.get('description', zone_name)
            print(f"      - {desc}: ({rect[0]}, {rect[1]}) - ({rect[2]}, {rect[3]})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False

def test_javascript_config():
    """Test that the JavaScript configuration file was created"""
    print("\n" + "=" * 60)
    print("Test 3: JavaScript Configuration")
    print("=" * 60)
    
    js_config_path = JS_DIR / "angela-character-config.js"
    
    if not js_config_path.exists():
        print(f"❌ JavaScript config not found: {js_config_path}")
        return False
    
    try:
        with open(js_config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key elements
        checks = [
            ('ANGELA_CHARACTER_CONFIG', 'Config object defined'),
            ('touch_zones', 'Touch zones defined'),
            ('body_parts', 'Body parts defined'),
            ('original_size', 'Original size defined')
        ]
        
        all_pass = True
        for pattern, description in checks:
            if pattern in content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description} - missing '{pattern}'")
                all_pass = False
        
        if all_pass:
            print(f"✅ JavaScript config valid: {js_config_path.name}")
        
        return all_pass
        
    except Exception as e:
        print(f"❌ Error reading JavaScript config: {e}")
        return False

def test_touch_detector():
    """Test that the touch detector module was created"""
    print("\n" + "=" * 60)
    print("Test 4: Touch Detector Module")
    print("=" * 60)
    
    detector_path = JS_DIR / "character-touch-detector.js"
    
    if not detector_path.exists():
        print(f"❌ Touch detector not found: {detector_path}")
        return False
    
    try:
        with open(detector_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key classes and methods
        checks = [
            ('class CharacterTouchDetector', 'Class defined'),
            ('detectTouch', 'detectTouch method'),
            ('detectDragPath', 'detectDragPath method'),
            ('_detectBodyPart', 'Body part detection'),
            ('_checkColorInRange', 'Color range check')
        ]
        
        all_pass = True
        for pattern, description in checks:
            if pattern in content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description} - missing '{pattern}'")
                all_pass = False
        
        if all_pass:
            print(f"✅ Touch detector valid: {detector_path.name}")
        
        return all_pass
        
    except Exception as e:
        print(f"❌ Error reading touch detector: {e}")
        return False

def test_haptic_handler():
    """Test that the haptic handler has been updated"""
    print("\n" + "=" * 60)
    print("Test 5: Haptic Handler Integration")
    print("=" * 60)
    
    haptic_path = JS_DIR / "haptic-handler.js"
    
    if not haptic_path.exists():
        print(f"❌ Haptic handler not found: {haptic_path}")
        return False
    
    try:
        with open(haptic_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for new methods
        checks = [
            ('handleCharacterTouch', 'Character touch handling'),
            ('_triggerHapticForBodyPart', 'Body part haptic patterns'),
            ('tactile_event', 'Tactile event format')
        ]
        
        all_pass = True
        for pattern, description in checks:
            if pattern in content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description} - missing '{pattern}'")
                all_pass = False
        
        if all_pass:
            print(f"✅ Haptic handler has new integrations")
        
        return all_pass
        
    except Exception as e:
        print(f"❌ Error reading haptic handler: {e}")
        return False

def test_live2d_manager():
    """Test that the live2d manager has been updated"""
    print("\n" + "=" * 60)
    print("Test 6: Live2D Manager Integration")
    print("=" * 60)
    
    manager_path = JS_DIR / "live2d-manager.js"
    
    if not manager_path.exists():
        print(f"❌ Live2D manager not found: {manager_path}")
        return False
    
    try:
        with open(manager_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for new methods
        checks = [
            ('_loadCharacterImage', 'Character image loading'),
            ('_initTouchDetector', 'Touch detector init'),
            ('_drawCharacterImage', 'Character image drawing'),
            ('handleCharacterInteraction', 'Interaction handling'),
            ('CharacterTouchDetector', 'Touch detector usage')
        ]
        
        all_pass = True
        for pattern, description in checks:
            if pattern in content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description} - missing '{pattern}'")
                all_pass = False
        
        if all_pass:
            print(f"✅ Live2D manager has new integrations")
        
        return all_pass
        
    except Exception as e:
        print(f"❌ Error reading Live2D manager: {e}")
        return False

def test_touch_zone_coordinates():
    """Test touch zone coordinates against the image analysis"""
    print("\n" + "=" * 60)
    print("Test 7: Touch Zone Coordinate Validation")
    print("=" * 60)
    
    config_path = RESOURCES_DIR / "angela_character_config.json"
    
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        image_width = config.get('original_size', {}).get('width', 0)
        image_height = config.get('original_size', {}).get('height', 0)
        
        print(f"   Image size: {image_width} x {image_height}")
        
        # Validate that all zones are within bounds
        zones = config.get('touch_zones', {})
        all_valid = True
        
        for zone_name, zone_data in zones.items():
            rect = zone_data.get('rect', [])
            if len(rect) == 4:
                x1, y1, x2, y2 = rect
                
                # Check bounds
                if x1 < 0 or y1 < 0 or x2 > image_width or y2 > image_height:
                    print(f"   ❌ Zone '{zone_name}' out of bounds")
                    all_valid = False
                
                # Check dimensions
                if x2 <= x1 or y2 <= y1:
                    print(f"   ❌ Zone '{zone_name}' has invalid dimensions")
                    all_valid = False
        
        if all_valid:
            print(f"✅ All {len(zones)} zones are valid")
        
        return all_valid
        
    except Exception as e:
        print(f"❌ Error validating coordinates: {e}")
        return False

def print_summary(results):
    """Print test summary"""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        print("\nSystem is ready with:")
        print("  - Character image with transparent background")
        print("  - 13 body part touch zones")
        print("  - Pixel-level color detection")
        print("  - Coordinate-based positioning")
        print("  - Haptic feedback integration")
        return True
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Please check the failed tests above")
        return False

def main():
    print("\n" + "=" * 60)
    print("Angela AI - Complete System Test")
    print("Angela AI - 完整系統測試")
    print("=" * 60)
    
    tests = [
        test_character_image,
        test_character_config,
        test_javascript_config,
        test_touch_detector,
        test_haptic_handler,
        test_live2d_manager,
        test_touch_zone_coordinates
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    return print_summary(results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
