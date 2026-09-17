"""
Angela Real Browser - Playwright Integration
真实浏览器控制模块 - 使用 Playwright

使用前确保：
1. pip install playwright
2. playwright install chromium
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING, cast

from core.utils import safe_error

# Type annotations for playwright - using string annotations to avoid mypy import errors
if TYPE_CHECKING:
    # Use string annotations to avoid importing playwright
    PLAYWRIGHT_AVAILABLE = True
else:
    # Runtime availability checked lazily
    PLAYWRIGHT_AVAILABLE = False


def _get_browser_viewport() -> dict:
    """Read browser viewport from bootstrap config."""
    try:
        from core.system.config.tiered_loader import get_config

        cfg = get_config("system/bootstrap")
        if not isinstance(cfg, dict):
            return {"width": 1920, "height": 1080}
        hardware_tiers = cfg.get("hardware_tiers", {}) or {}
        default_tier = hardware_tiers.get("default", {}) or {}
        screen = default_tier.get("screen", {}) or {}
        return {"width": screen.get("width", 1920), "height": screen.get("height", 1080)}
    except Exception:
        return {"width": 1920, "height": 1080}

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


# Runtime availability check
def _check_playwright_available() -> bool:
    try:
        import importlib
        importlib.import_module("playwright.async_api")
        return True
    except ImportError:
        return False


# Runtime import
def _get_async_playwright() -> Any:
    """Lazily import playwright at runtime."""
    try:
        import importlib
        pw_module = importlib.import_module("playwright.async_api")
        return pw_module.async_playwright
    except ImportError:
        return None


logger = logging.getLogger(__name__)


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
        self.playwright: Optional[Any] = None
        self.browser: Optional[Any] = None
        self.context: Optional[Any] = None
        self.page: Optional[Any] = None

    async def initialize(self) -> bool:
        """初始化浏览器"""
        if not _check_playwright_available():
            logger.error("❌ Playwright 未安裝，請執行: pip install playwright && playwright install chromium")
            return False
            
        try:
            ap = _get_async_playwright()
            if ap is None:
                logger.error("❌ Playwright import failed")
                return False
            playwright = await ap().start()
            self.playwright = playwright

            if self.headless:
                self.browser = await playwright.chromium.launch(headless=True)
            else:
                self.browser = await playwright.chromium.launch(headless=False)

            if self.browser is None:
                logger.error("❌ 瀏覽器啟動失敗")
                return False

            self.context = await self.browser.new_context(
                viewport=_get_browser_viewport(),
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )

            if self.context is None:
                logger.error("❌ 瀏覽器上下文創建失敗")
                return False

            self.page = await self.context.new_page()

            if self.page is None:
                logger.error("❌ 頁面創建失敗")
                return False

            logger.info("✅ 瀏覽器已初始化")
            return True

        except (
            Exception
        ) as e:  # broad exception acceptable: browser launch may fail for various reasons
            logger.error(f"❌ 瀏覽器初始化失敗: {e}", exc_info=True)
            return False

    async def close(self) -> None:
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
        self.browser = None
        self.context = None
        self.playwright = None
        logger.info("✅ 瀏覽器已關閉")

    async def browse_tutorial(self, url: str) -> Optional[Tutorial]:
        """
        浏览教程页面并提取内容

        Args:
            url: 教程页面 URL

        Returns:
            Tutorial 对象 或 None
        """
        if self.page is None:
            logger.error("❌ 頁面未初始化")
            return None
            
        try:
            await self.page.goto(url, timeout=30020)
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

        except (
            Exception
        ) as e:  # broad exception acceptable: page navigation may fail or content extraction errors
            logger.error(f"❌ 教程提取失敗: {e}", exc_info=True)
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
        if self.page is None:
            logger.error("❌ 頁面未初始化")
            return []
            
        artworks = []

        try:
            await self.page.goto(url, timeout=30020)
            await self.page.wait_for_load_state("networkidle")

            images = await self.page.evaluate(f"""
                () => {{
                    const items = document.querySelectorAll('img');
                    const results = [];
                    for (let item of items) {{
                        if (item.src && item.src.startswith('http')) {{
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

            logger.info(f"✅ 收集到 {len(artworks)} 個作品")

        except (
            Exception
        ) as e:  # broad exception acceptable: artwork collection should be resilient to extraction errors
            logger.error(f"❌ 作品收集失敗: {e}", exc_info=True)

        return artworks

    async def analyze_style(self, image_url: str) -> Dict[str, Any]:
        """
        分析图片风格特征

        Args:
            image_url: 图片 URL

        Returns:
            风格分析结果
        """
        if self.page is None:
            logger.error("❌ 頁面未初始化")
            return {"error": "Page not initialized"}
            
        try:
            await self.page.goto(image_url, timeout=30020)
            await self.page.wait_for_load_state("networkidle")

            analysis: Dict[str, Any] = await self.page.evaluate("""
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

        except (
            Exception
        ) as e:  # broad exception acceptable: style analysis should be resilient to page errors
            logger.error(f"❌ 風格分析失敗: {e}", exc_info=True)
            return {"error": safe_error(e)}

    async def search_art_tutorials(self, query: str) -> List[Dict]:
        """
        搜索艺术教程

        Args:
            query: 搜索关键词

        Returns:
            搜索结果列表
        """
        if self.page is None:
            logger.error("❌ 頁面未初始化")
            return []
            
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}+art+tutorial"

        try:
            await self.page.goto(search_url, timeout=30020)
            await self.page.wait_for_load_state("networkidle")

            results: List[Dict] = await self.page.evaluate("""
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

        except (
            Exception
        ) as e:  # broad exception acceptable: search should be resilient to network errors
            logger.error(f"❌ 搜索失敗: {e}", exc_info=True)
            return []

    async def take_screenshot(self, path: Optional[str] = None) -> str:
        """
        截图当前页面

        Args:
            path: 保存路径 (可选)

        Returns:
            截图路径
        """
        if self.page is None:
            logger.error("❌ 頁面未初始化")
            return ""
            
        if not path:
            from datetime import datetime

            path = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        # path is guaranteed to be str at this point
        result_path: str = path
        await self.page.screenshot(path=result_path)
        logger.info(f"✅ 截圖已保存: {result_path}")
        return result_path

    async def get_page_html(self) -> str:
        """获取页面 HTML"""
        if self.page is None:
            logger.error("❌ 頁面未初始化")
            return ""
        return cast(str, await self.page.content())


async def test_browser() -> None:
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

    except (
        Exception
    ) as e:  # broad exception acceptable: browser test should handle initialization failures gracefully
        logger.exception("❌ 测试失败: %s", e)


if __name__ == "__main__":
    asyncio.run(test_browser())
