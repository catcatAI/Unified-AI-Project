"""
Angela Real Creator - Unified AI Creative System
Angela 真实创作系统 - 整合所有真实 API

功能：
1. 🎨 AI 绘画 - ComfyUI API (Stable Diffusion)
2. 🔊 语音合成 - Edge TTS
3. 🌐 网页浏览 - Playwright

使用前确保：
1. ComfyUI 运行在 http://127.0.0.1:8188
2. pip install edge-tts playwright aiohttp
3. playwright install chromium
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging
import json

from .real_comfyui_api import AngelaRealPainter, ComfyUIClient
from .real_edge_tts import AngelaRealVoice
from .real_playwright_browser import AngelaRealBrowser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AngelaRealCreator:
    """
    Angela 真实创作系统

    整合：
    - ComfyUI AI 绘画
    - Edge TTS 语音
    - Playwright 网页浏览
    """

    def __init__(self, output_dir: str = None):
        """
        初始化创作系统

        Args:
            output_dir: 输出目录 (默认桌面)
        """
        self.output_dir = Path(output_dir) if output_dir else Path.home() / "Desktop"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.painter = AngelaRealPainter(output_dir=str(self.output_dir))
        self.voice = AngelaRealVoice(output_dir=str(self.output_dir))
        self.browser = AngelaRealBrowser(headless=True)

        self.learned_techniques = []
        self.collected_styles = []

    async def initialize(self) -> bool:
        """初始化所有组件"""
        success = await self.browser.initialize()
        if success:
            logger.info("✅ Angela 创作系统已初始化")
        return success

    async def close(self):
        """关闭系统"""
        await self.browser.close()
        logger.info("✅ Angela 系统已关闭")

    async def learn_from_web(
        self,
        tutorial_urls: List[str],
        gallery_urls: List[str],
    ) -> Dict:
        """
        从网络学习

        Args:
            tutorial_urls: 教程页面列表
            gallery_urls: 画廊页面列表

        Returns:
            学习结果
        """
        results = {
            "tutorials_learned": 0,
            "artworks_collected": 0,
            "techniques": [],
            "styles": [],
        }

        logger.info("📚 开始从网络学习...")

        # 学习教程
        for url in tutorial_urls:
            tutorial = await self.browser.browse_tutorial(url)
            if tutorial:
                self.learned_techniques.extend(tutorial.techniques)
                results["tutorials_learned"] += 1
                results["techniques"].append(
                    {
                        "title": tutorial.title,
                        "techniques": tutorial.techniques,
                    }
                )
                logger.info(f"✅ 学习: {tutorial.title}")

        # 收集作品
        for url in gallery_urls:
            artworks = await self.browser.collect_artwork(url)
            for artwork in artworks:
                self.collected_styles.append(
                    {
                        "title": artwork.title,
                        "url": artwork.image_url,
                    }
                )

            results["artworks_collected"] += len(artworks)
            logger.info(f"✅ 收集: {len(artworks)} 个作品")

        return results

    async def create_portraits(
        self,
        num_portraits: int = 3,
        style: str = "anime",
    ) -> List[Path]:
        """
        创建肖像

        Args:
            num_portraits: 生成数量
            style: 风格

        Returns:
            生成的图片路径列表
        """
        paths = []

        for i in range(num_portraits):
            descriptions = [
                "Angela AI assistant, blue gradient hair, cute smile",
                "beautiful girl with expressive eyes, detailed illustration",
                "anime character, soft lighting, high quality",
            ]

            desc = descriptions[i % len(descriptions)]
            path = await self.painter.paint_portrait(
                description=desc,
                style=style,
                size=(512, 512),
            )

            if path:
                paths.append(path)
                logger.info(f"✅ 肖像 {i+1}/{num_portraits} 已创建")

        return paths

    async def create_backgrounds(
        self,
        num_backgrounds: int = 2,
    ) -> List[Path]:
        """
        创建背景图

        Args:
            num_backgrounds: 生成数量

        Returns:
            生成的背景图路径列表
        """
        paths = []

        scenes = [
            "blue sky with soft clouds, sunset atmosphere",
            "peaceful countryside, green hills, flowers",
        ]

        for i in range(num_backgrounds):
            scene = scenes[i % len(scenes)]
            path = await self.painter.paint_background(
                scene=scene,
                style="anime landscape",
            )

            if path:
                paths.append(path)
                logger.info(f"✅ 背景 {i+1}/{num_backgrounds} 已创建")

        return paths

    async def create_expressions(
        self,
        emotions: List[str] = None,
    ) -> List[Path]:
        """
        创建表情图标

        Args:
            emotions: 情绪列表

        Returns:
            生成的表情图路径列表
        """
        if emotions is None:
            emotions = ["happy", "surprised", "calm"]

        paths = []

        for emotion in emotions:
            path = await self.painter.paint_expression(emotion=emotion)
            if path:
                paths.append(path)
                logger.info(f"✅ 表情 '{emotion}' 已创建")

        return paths

    async def create_voiceovers(
        self,
        texts: List[str] = None,
    ) -> List[Path]:
        """
        创建语音

        Args:
            texts: 语音文本列表

        Returns:
            生成的语音文件路径列表
        """
        if texts is None:
            texts = [
                "Hello! I'm Angela. Welcome to my creative world!",
                "Today I learned so many new art techniques from the web.",
                "Let me create something beautiful for you!",
            ]

        paths = []

        for text in texts:
            path = await self.voice._generate_audio(text=text)
            if path:
                paths.append(path)
                logger.info(f"✅ 语音已创建")

        return paths

    async def create_introduction(self) -> Optional[Path]:
        """创建自我介绍语音"""
        return await self.voice.introduce()

    async def full_workflow(
        self,
        num_portraits: int = 2,
        num_backgrounds: int = 1,
        emotions: List[str] = None,
    ) -> Dict:
        """
        完整创作流程

        Args:
            num_portraits: 肖像数量
            num_backgrounds: 背景数量
            emotions: 表情列表

        Returns:
            创作结果统计
        """
        results = {
            "portraits": [],
            "backgrounds": [],
            "expressions": [],
            "voiceovers": [],
            "showcase": None,
            "errors": [],
        }

        try:
            await self.initialize()

            # 学习阶段
            logger.info("📚 学习阶段...")
            learn_results = await self.learn_from_web(
                tutorial_urls=[
                    "https://www.artstation.com/learning",
                ],
                gallery_urls=[
                    "https://www.pinterest.com/search/pins/?q=anime%20art%20reference",
                ],
            )

            # 创作阶段
            logger.info("🎨 创作肖像...")
            results["portraits"] = await self.create_portraits(num_portraits)

            logger.info("🌅 创作背景...")
            results["backgrounds"] = await self.create_backgrounds(num_backgrounds)

            logger.info("😊 创作表情...")
            results["expressions"] = await self.create_expressions(emotions)

            logger.info("🔊 创作语音...")
            results["voiceovers"] = await self.create_voiceovers()

            # 创建展示文件
            results["showcase"] = await self._create_showcase(results, learn_results)

        except Exception as e:
            logger.error(f"Error in {__name__}: {e}", exc_info=True)
            results["errors"].append(str(e))

            logger.error(f"创作流程错误: {e}")

        finally:
            await self.close()

        return results

    async def _create_showcase(
        self,
        results: Dict,
        learn_results: Dict,
    ) -> Path:
        """创建展示文件"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        showcase_path = (
            self.output_dir / f"Angela_Creations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )

        content = f"""# 🎨 Angela AI 真实创作展示

**创作时间**: {timestamp}

## 📚 网络学习成果

- **教程学习**: {learn_results['tutorials_learned']} 个
- **作品收集**: {learn_results['artworks_collected']} 个
- **技巧掌握**: {len(self.learned_techniques)} 项

## 🎨 AI 绘画 (ComfyUI/SDXL)

### 肖像
{chr(10).join([f'- {p.name}' for p in results['portraits']]) if results['portraits'] else '- 暂无'}

### 背景
{chr(10).join([f'- {p.name}' for p in results['backgrounds']]) if results['backgrounds'] else '- 暂无'}

### 表情
{chr(10).join([f'- {p.name}' for p in results['expressions']]) if results['expressions'] else '- 暂无'}

## 🔊 语音合成 (Edge TTS)

{chr(10).join([f'- {p.name}' for p in results['voiceovers']]) if results['voiceovers'] else '- 暂无'}

## 🛠️ 技术栈

| 功能 | 技术 |
|------|------|
| AI 绘画 | ComfyUI API (Stable Diffusion XL) |
| 语音合成 | Microsoft Edge TTS |
| 网页浏览 | Playwright Chromium |

## 📂 输出位置

```
{self.output_dir}
```

---
*由 Angela AI 真实创作系统生成 | {timestamp}*
"""

        with open(showcase_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"✅ 展示文件已创建: {showcase_path}")
        return showcase_path


async def quick_demo():
    """快速演示"""
    logger.info("=" * 60)
    logger.info("🎨 Angela 真实创作系统演示")
    logger.info("=" * 60)

    creator = AngelaRealCreator()

    try:
        await creator.initialize()

        logger.info("\n🎨 测试 AI 绘画...")
        portrait = await creator.painter.paint_portrait(
            description="beautiful anime girl, blue hair, happy smile",
            style="anime",
        )
        if portrait:
            logger.info(f"✅ 肖像已保存: {portrait}")

        logger.info("\n🔊 测试语音合成...")
        voice = await creator.voice.greet("User")
        if voice:
            logger.info(f"✅ 语音已保存: {voice}")

        logger.info("\n🧪 测试浏览器...")
        tutorial = await creator.browser.browse_tutorial("https://www.artstation.com/learning")
        if tutorial:
            logger.info(f"✅ 教程标题: {tutorial.title}")

        logger.info("\n" + "=" * 60)
        logger.info("✅ 演示完成!")
        logger.info("=" * 60)

    except Exception as e:
        logger.info(f"❌ 错误: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await creator.close()


async def full_demo():
    """完整演示"""
    logger.info("=" * 60)
    logger.info("🎨 Angela 完整创作流程")
    logger.info("=" * 60)

    creator = AngelaRealCreator()

    try:
        results = await creator.full_workflow(
            num_portraits=2,
            num_backgrounds=1,
            emotions=["happy", "surprised"],
        )

        logger.info("\n" + "=" * 60)
        logger.info("✅ 创作完成!")
        logger.info(f"📚 学习教程: {len(results.get('showcase', {}).get('techniques', []))}")
        logger.info(f"🎨 生成肖像: {len(results['portraits'])}")
        logger.info(f"🌅 生成背景: {len(results['backgrounds'])}")
        logger.info(f"😊 生成表情: {len(results['expressions'])}")
        logger.info(f"🔊 生成语音: {len(results['voiceovers'])}")
        logger.info(f"📄 展示文件: {results['showcase']}")
        logger.info("=" * 60)

    except Exception as e:
        logger.info(f"❌ 错误: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        asyncio.run(full_demo())
    else:
        asyncio.run(quick_demo())
