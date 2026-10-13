# Angela AI 创作系统

## 概述

Angela AI 的创作系统整合了真实的 AI API，提供高质量的绘画、语音和网页浏览功能。

## 模块结构

```
core/art/
├── real_edge_tts.py           # Edge TTS (语音合成)
└── real_playwright_browser.py # Playwright (网页浏览)

> ⚠️ **2026-10 更正**：本模块曾包含 `desktop_demo.py`、`real_creator.py` 与
> `real_comfyui_api.py`，三者均已从仓库移除。以下描述它们的章节保留为**历史记录**，
> 其中的命令已不可执行。
```

## 快速开始

### 桌面演示（`desktop_demo.py` 已移除）

原桌面演示的输出示例（保留作为参考）：

```
🎨 Angela 开始创作...
📂 保存位置: C:\Users\catai\OneDrive\Desktop

1️⃣  创作美术作品...
   🖼️  绘制自画像...
   ✅ 保存: Angela_SelfPortrait_20260204_094543.png
   😊 绘制快乐表情...
   ✅ 保存: Angela_Happy_20260204_094543.png
   🌅 绘制背景图...
   ✅ 保存: Angela_Background_20260204_094543.png
```

### 运行现存模块

```bash
# 安装依赖（edge-tts 已在 BASE 依赖中，无需重复安装）
pip install playwright aiohttp

# 安装 Playwright 浏览器
playwright install chromium
```

现存的 `real_edge_tts.py` 与 `real_playwright_browser.py`
以 import 方式使用，用法见下方「模块说明」。

## 模块说明

### ~~desktop_demo.py~~（已移除）

> 该模块已从仓库移除；以下为历史功能说明。

使用 PIL 绘制简单图像，无需外部服务。

**功能:**

- 绘制自画像
- 绘制表情图标
- 绘制背景图
- 生成说明文件

### ~~real_comfyui_api.py~~（已移除）

> 该模块已从仓库移除；以下为历史功能说明。

ComfyUI API 集成，用于 AI 绘画。

**依赖:**

- ComfyUI 运行在 http://127.0.0.1:8188
- 安装了 Stable Diffusion 模型

**使用示例:**

```python
from apps.backend.src.core.art.real_comfyui_api import AngelaRealPainter

painter = AngelaRealPainter()

# 生成肖像
path = await painter.paint_portrait(
    description="beautiful anime girl, blue hair",
    style="anime",
    size=(512, 512)
)

# 生成背景
path = await painter.paint_background(
    scene="blue sky with clouds",
    style="anime landscape"
)

# 生成表情
path = await painter.paint_expression(
    emotion="happy"
)
```

### real_edge_tts.py

Microsoft Edge TTS 集成，用于高质量语音合成。

**依赖:**

- Windows 系统
- pip install edge-tts

**使用示例:**

```python
from apps.backend.src.core.art.real_edge_tts import AngelaRealVoice

voice = AngelaRealVoice()

# 生成问候
path = await voice.greet("User")

# 生成带情绪的语音
path = await voice.express_emotion("happy")
```

### real_playwright_browser.py

Playwright 浏览器控制，用于网页浏览和学习。

**依赖:**

- pip install playwright
- playwright install chromium

**使用示例:**

```python
from apps.backend.src.core.art.real_playwright_browser import AngelaRealBrowser

browser = AngelaRealBrowser(headless=True)
await browser.initialize()

# 浏览教程
tutorial = await browser.browse_tutorial("https://www.artstation.com/learning")

# 收集作品
artworks = await browser.collect_artwork("https://www.pinterest.com/search/pins/?q=anime%20art")

await browser.close()
```

### ~~real_creator.py~~（已移除）

> 该模块已从仓库移除；以下为历史功能说明。

整合所有创作功能的统一系统。

**功能:**

- 从网络学习教程和作品
- 生成 AI 绘画作品
- 生成配套语音
- 创建展示文件

## 文件输出位置

所有文件默认保存到桌面:

```
C:\Users\<用户名>\OneDrive\Desktop\
├── Angela_SelfPortrait_*.png
├── Angela_Happy_*.png
├── Angela_Surprised_*.png
├── Angela_Background_*.png
└── Angela_Creations_*.md
```

## 依赖安装

```bash
# 核心依赖
pip install pillow aiohttp

# 语音合成 (Windows)
pip install edge-tts

# 网页浏览
pip install playwright
playwright install chromium

# AI 绘画 (可选，需要 ComfyUI)
# 参见: https://github.com/comfyanonymous/ComfyUI
```

## 版本历史

| 版本  | 日期       | 描述                                                                        |
| ----- | ---------- | --------------------------------------------------------------------------- |
| 1.0.0 | 2026-02-04 | 初始版本，添加 desktop_demo                                                 |
| 1.1.0 | 2026-02-04 | 添加 real_creator, real_comfyui_api, real_edge_tts, real_playwright_browser |

## 许可证

MIT License
