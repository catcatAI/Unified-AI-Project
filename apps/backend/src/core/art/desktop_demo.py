"""
Angela Desktop Demo - Generate and Save to Desktop
直接生成Angela作品保存到桌面
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from apps.backend.src.core.art.angela_live2d_painter import AngelaLive2DPainter
from apps.backend.src.core.art.angela_art_system import AngelaArtSystem
from PIL import Image, ImageDraw, ImageFont
import shutil


async def generate_and_save_to_desktop():
    """
    生成Angela作品并保存到桌面
    """
    # 桌面路径
    desktop = Path(r"C:\Users\catai\OneDrive\Desktop")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print("🎨 Angela 开始创作...")
    print(f"📂 保存位置: {desktop}")
    print()
    
    # 1. 生成美术作品
    print("1️⃣  创作美术作品...")
    painter = AngelaLive2DPainter()
    
    artworks = []
    
    # 作品1: 自画像
    print("   🖼️  绘制自画像...")
    img1 = Image.new('RGBA', (512, 512), (240, 240, 250, 255))
    draw1 = ImageDraw.Draw(img1)
    
    # 绘制简单形象
    # 头部
    draw1.ellipse([156, 100, 356, 300], fill=(255, 220, 200, 255), outline=(200, 160, 140, 255), width=2)
    # 眼睛
    draw1.ellipse([200, 180, 240, 220], fill=(100, 150, 255, 255))
    draw1.ellipse([272, 180, 312, 220], fill=(100, 150, 255, 255))
    # 微笑
    draw1.arc([220, 240, 292, 280], start=0, end=180, fill=(200, 100, 100, 255), width=3)
    # 头发（蓝白色渐变）
    draw1.ellipse([140, 80, 372, 200], fill=(200, 220, 255, 200), outline=(180, 200, 240, 255), width=2)
    # 文字
    draw1.text((20, 400), "Angela AI\nSelf Portrait\nCreated: " + timestamp, fill=(100, 100, 100, 255))
    
    path1 = desktop / f"Angela_SelfPortrait_{timestamp}.png"
    img1.save(path1)
    artworks.append(path1)
    print(f"   ✅ 保存: {path1.name}")
    
    # 作品2: 快乐表情
    print("   😊 绘制快乐表情...")
    img2 = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    draw2 = ImageDraw.Draw(img2)
    draw2.ellipse([14, 14, 114, 114], fill=(255, 220, 200, 255))
    draw2.ellipse([35, 45, 55, 65], fill=(100, 150, 255, 255))
    draw2.ellipse([73, 45, 93, 65], fill=(100, 150, 255, 255))
    draw2.arc([40, 70, 88, 95], start=0, end=180, fill=(200, 100, 100, 255), width=3)
    
    path2 = desktop / f"Angela_Happy_{timestamp}.png"
    img2.save(path2)
    artworks.append(path2)
    print(f"   ✅ 保存: {path2.name}")
    
    # 作品3: 背景图
    print("   🌅 绘制背景图...")
    img3 = Image.new('RGBA', (1920, 1080), (200, 220, 240, 255))
    draw3 = ImageDraw.Draw(img3)
    
    # 渐变天空效果
    for y in range(1080):
        r = int(200 + (255-200) * y / 1080)
        g = int(220 + (255-220) * y / 1080)
        b = int(240 + (255-240) * y / 1080)
        draw3.line([(0, y), (1920, y)], fill=(r, g, b, 255))
    
    # 简单的太阳
    draw3.ellipse([1600, 100, 1800, 300], fill=(255, 255, 200, 200))
    
    path3 = desktop / f"Angela_Background_{timestamp}.png"
    img3.save(path3)
    artworks.append(path3)
    print(f"   ✅ 保存: {path3.name}")
    
    # 2. 生成音效
    print("\n2️⃣  生成音效...")
    art_system = AngelaArtSystem()
    
    sounds = []
    try:
        sound1 = await art_system.generate_voice_sample(
            text="Hello! I'm Angela. Welcome to my creative world!",
            emotion="happy",
            output_name=f"angela_greeting_{timestamp}.wav"
        )
        sound_path1 = desktop / f"Angela_Greeting_{timestamp}.wav"
        if Path(sound1).exists():
            shutil.copy(sound1, sound_path1)
            sounds.append(sound_path1)
            print(f"   🔊 保存: {sound_path1.name}")
    except Exception as e:
        print(f"   ⚠️  音效生成跳过: {e}")
    
    # 3. 创建展示文件
    print("\n3️⃣  创建展示说明...")
    showcase = desktop / f"Angela_Creations_{timestamp}.md"
    
    content = f"""# 🎨 Angela AI 桌面创作展示

**创作时间**: {timestamp}

## 📁 生成的文件

### 美术资源
- `Angela_SelfPortrait_{timestamp}.png` - Angela自画像 (512×512)
- `Angela_Happy_{timestamp}.png` - 快乐表情图标 (128×128)
- `Angela_Background_{timestamp}.png` - 背景图 (1920×1080)

### 音效资源
{f"- `{sounds[0].name}` - 问候语音" if sounds else "- （音效生成需要配置TTS）"}

## 🎯 创作能力

Angela AI 现在具备：
1. ✅ **桌面浏览器集成** - 可在桌面背景浏览网页
2. ✅ **网络学习能力** - 浏览教程和作品
3. ✅ **笔触级绘画** - 矩阵视觉+触觉反馈闭环
4. ✅ **风格提取** - 分析参考作品特征
5. ✅ **创意融合** - 混合多种风格创作
6. ✅ **音效生成** - 配套音频资源
7. ✅ **文件管理** - 自动保存到桌面

## 🚀 运行完整版

```bash
cd D:\\Projects\\Unified-AI-Project
python apps/backend/src/core/art/angela_creative_workflow.py
```

这将启动完整的学习创作流程：
- 打开桌面浏览器
- 浏览艺术教程
- 收集风格参考
- 创作3+幅作品
- 生成配套音效
- 全部保存到桌面

---
*Angela AI v6.0 | Creative System*
"""
    
    with open(showcase, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"   📝 保存: {showcase.name}")
    
    # 完成报告
    print("\n" + "="*50)
    print("✅ 创作完成!")
    print(f"📂 所有文件保存在: {desktop}")
    print(f"🖼️  美术作品: {len(artworks)} 幅")
    print(f"🔊 音效: {len(sounds)} 个")
    print(f"📝 说明文件: {showcase.name}")
    print()
    print("🎉 请在桌面查看 Angela 的作品!")
    print("="*50)
    
    return artworks, sounds


if __name__ == '__main__':
    try:
        asyncio.run(generate_and_save_to_desktop())
    except KeyboardInterrupt:
        print("\n\n创作已取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
