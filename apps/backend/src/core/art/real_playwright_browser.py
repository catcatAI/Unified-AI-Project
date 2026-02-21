"""
Angela Real Browser - Playwright Integration
真实浏览器控制模块 - 使用 Playwright

使用前确保：
1. pip install playwright
2. playwright install chromium
"""

import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class Tutorial:
    """教程信息"""

    title: str
    url: str
    content: str
    techniques: List[str]


@dataclass
class Artwork:
    """作品信息"""

    title: str
    url: str
    image_url: str
    artist: str
    style: str


class AngelaRealBrowser:
    """
    Angela 真实浏览器系统
    使用 Playwright 进行真正的网页浏览和内容提取
    """

    def __init__(self, headless: bool = True):
        """
        初始化浏览器

        Args:
            headless: 是否无头模式运行
        """
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None

    async def initialize(self):
        """初始化浏览器"""
        try:
            from playwright.async_api import async_playwright

            playwright = await async_playwright().start()

            if self.headless:
                self.browser = await playwright.chromium.launch(headless=True)
            else:
                self.browser = await playwright.chromium.launch(headless=False)

            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )

            self.page = await self.context.new_page()

            logger.info("✅ 浏览器已初始化")
            return True

        except Exception as e:
            logger.error(f"❌ 浏览器初始化失败: {e}")
            return False

    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            logger.info("✅ 浏览器已关闭")

    async def browse_tutorial(self, url: str) -> Optional[Tutorial]:
        """
        浏览教程页面并提取内容

        Args:
            url: 教程页面 URL

        Returns:
            Tutorial 对象 或 None
        """
        try:
            await self.page.goto(url, timeout=30000)
            await self.page.wait_for_load_state("networkidle")

            title = await self.page.title()

            content = await self.page.evaluate("""
                () => {
                    const text = document.body.innerText;
                    return text.slice(0, 5000);
                }
            """)

            techniques = await self.page.evaluate("""
                () => {
                    const keywords = ['technique', 'method', 'step', 'guide', 'tutorial', 'how to'];
                    const text = document.body.innerText.toLowerCase();
                    const found = keywords.filter(k => text.includes(k));
                    return found.slice(0, 5);
                }
            """)

            logger.info(f"✅ 教程已提取: {title}")

            return Tutorial(
                title=title,
                url=url,
                content=content,
                techniques=techniques,
            )

        except Exception as e:
            logger.error(f"❌ 教程提取失败: {e}")
            return None

    async def collect_artwork(self, url: str, max_images: int = 10) -> List[Artwork]:
        """
        从画廊页面收集作品

        Args:
            url: 画廊页面 URL
            max_images: 最大收集数量

        Returns:
            Artwork 列表
        """
        artworks = []

        try:
            await self.page.goto(url, timeout=30000)
            await self.page.wait_for_load_state("networkidle")

            images = await self.page.evaluate(f"""
                () => {{
                    const items = document.querySelectorAll('img');
                    const results = [];
                    for (let item of items) {{
                        if (item.src && item.src.startsWith('http')) {{
                            results.push({{
                                src: item.src,
                                alt: item.alt || 'Untitled',
                                width: item.naturalWidth,
                                height: item.naturalHeight,
                            }});
                        }}
                    }}
                    return results.slice(0, {max_images});
                }}
            """)

            for img in images:
                artworks.append(
                    Artwork(
                        title=img["alt"],
                        url=url,
                        image_url=img["src"],
                        artist="Unknown",
                        style="Unknown",
                    )
                )

            logger.info(f"✅ 收集到 {len(artworks)} 个作品")

        except Exception as e:
            logger.error(f"❌ 作品收集失败: {e}")

        return artworks

    async def analyze_style(self, image_url: str) -> Dict[str, Any]:
        """
        分析图片风格特征

        Args:
            image_url: 图片 URL

        Returns:
            风格分析结果
        """
        try:
            await self.page.goto(image_url, timeout=30000)
            await self.page.wait_for_load_state("networkidle")

            analysis = await self.page.evaluate("""
                () => {
                    const img = document.querySelector('img');
                    if (!img) return { error: 'No image found' };
                    
                    return {
                        width: img.naturalWidth,
                        height: img.naturalHeight,
                        aspectRatio: img.naturalWidth / img.naturalHeight,
                        src: img.src,
                    };
                }
            """)

            return analysis

        except Exception as e:
            logger.error(f"❌ 风格分析失败: {e}")
            return {"error": str(e)}

    async def search_art_tutorials(self, query: str) -> List[Dict]:
        """
        搜索艺术教程

        Args:
            query: 搜索关键词

        Returns:
            搜索结果列表
        """
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}+art+tutorial"

        try:
            await self.page.goto(search_url, timeout=30000)
            await self.page.wait_for_load_state("networkidle")

            results = await self.page.evaluate("""
                () => {
                    const items = document.querySelectorAll('div.g');
                    const results = [];
                    for (let item of items) {
                        const title = item.querySelector('h3');
                        const link = item.querySelector('a');
                        const snippet = item.querySelector('.VwiC3b');
                        if (title && link) {
                            results.push({
                                title: title.innerText,
                                url: link.href,
                                snippet: snippet ? snippet.innerText.slice(0, 200) : '',
                            });
                        }
                    }
                    return results.slice(0, 5);
                }
            """)

            return results

        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}")
            return []

    async def take_screenshot(self, path: str = None) -> str:
        """
        截图当前页面

        Args:
            path: 保存路径 (可选)

        Returns:
            截图路径
        """
        if not path:
            from datetime import datetime

            path = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        await self.page.screenshot(path=path)
        logger.info(f"✅ 截图已保存: {path}")
        return path

    async def get_page_html(self) -> str:
        """获取页面 HTML"""
        return await self.page.content()


async def test_browser():
    """测试浏览器"""
    logger.info("🧪 测试 Playwright 浏览器...")

    browser = AngelaRealBrowser(headless=True)

    try:
        success = await browser.initialize()
        if not success:
            logger.info("❌ 浏览器初始化失败")
            return

        logger.info("✅ 浏览器初始化成功")
        logger.info("\n🔍 测试浏览教程...")

        tutorial = await browser.browse_tutorial("https://www.artstation.com/learning")
        if tutorial:
            logger.info(f"✅ 教程标题: {tutorial.title}")
            logger.info(f"📚 学到的技巧: {tutorial.techniques}")

        logger.info("\n🎨 测试收集作品...")
        artworks = await browser.collect_artwork(
            "https://www.pinterest.com/search/pins/?q=anime%20art"
        )
        logger.info(f"✅ 收集到 {len(artworks)} 个作品")

        await browser.close()
        logger.info("\n✅ 测试完成!")

    except Exception as e:
        logger.info(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    import sys

    asyncio.run(test_browser())
