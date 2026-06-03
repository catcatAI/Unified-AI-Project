"""
Angela AI v6.0 - Browser Controller
浏览器控制器

Manages web browsing activities including search, content extraction,
game detection, and bookmark management.

Features:
- Web search with multiple engines
- Content extraction and summarization
- Browser game detection
- Bookmark management

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import asyncio
import logging
import aiohttp
from bs4 import BeautifulSoup
from core.system.config.magic_numbers import timeout_value
from core.system.config.async_io import async_write_text, async_read_text

logger = logging.getLogger(__name__)


class SearchEngine(Enum):
    """搜索引擎 / Search engines"""

    GOOGLE = ("Google", "https://www.google.com/search")
    BING = ("Bing", "https://www.bing.com/search")
    DUCKDUCKGO = ("DuckDuckGo", "https://duckduckgo.com/")
    BAIDU = ("百度", "https://www.baidu.com/s")

    def __init__(self, name: str, search_url: str):
        self.search_name = name
        self.search_url = search_url


class BrowserState(Enum):
    """浏览器状态 / Browser states"""

    IDLE = ("空闲", "Idle")
    NAVIGATING = ("导航中", "Navigating")
    LOADING = ("加载中", "Loading")
    INTERACTING = ("交互中", "Interacting")
    PLAYING_GAME = ("游戏中", "Playing Game")

    def __init__(self, cn_name: str, en_name: str):
        self.cn_name = cn_name
        self.en_name = en_name


@dataclass
class SearchResult:
    """搜索结果 / Search result"""

    title: str
    url: str
    snippet: str
    relevance_score: float = 0.0
    source_engine: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExtractedContent:
    """提取的内容 / Extracted content"""

    url: str
    title: str
    text_content: str
    images: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    word_count: int = 0


@dataclass
class Bookmark:
    """书签 / Bookmark"""

    bookmark_id: str
    title: str
    url: str
    category: str = "未分类"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    visit_count: int = 0
    last_visited: Optional[datetime] = None
    notes: str = ""


@dataclass
class GameSession:
    """游戏会话 / Game session"""

    game_name: str
    game_url: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_minutes: float = 0.0
    is_active: bool = True


class BrowserController:
    """
    浏览器控制器主类 / Main browser controller class

    Manages web browsing activities for Angela AI including search operations,
    content extraction, game detection, and bookmark management.

    Attributes:
        current_state: Current browser state
        active_search_results: Current search results
        bookmarks: Bookmark collection
        game_sessions: Detected game sessions
        search_history: History of searches

    Example:
        >>> browser = BrowserController()
        >>> await browser.initialize()
        >>>
        >>> # Perform search
        >>> results = await browser.search("artificial intelligence news")
        >>> for result in results:
        ...     print(f"{result.title}: {result.url}")
        >>>
        >>> # Extract content
        >>> content = await browser.extract_content("https://example.com")
        >>> print(content.summary)
        >>>
        >>> # Check if playing game
        >>> if browser.is_playing_game():
        ...     print(f"Currently playing: {browser.get_active_game().game_name}")
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # State
        self.current_state: BrowserState = BrowserState.IDLE
        self.default_engine: SearchEngine = SearchEngine.GOOGLE

        # Data
        self.active_search_results: List[SearchResult] = []
        self.bookmarks: Dict[str, Bookmark] = {}
        self.game_sessions: List[GameSession] = []
        self.search_history: List[Dict[str, Any]] = []

        # Game detection
        self.game_keywords = [
            "game",
            "play",
            "gaming",
            "casino",
            "poker",
            "slots",
            "minecraft",
            "fortnite",
            "roblox",
            "steam",
            "epic games",
        ]
        self.current_game: Optional[GameSession] = None

        # Callbacks
        self._state_change_callbacks: List[Callable[[BrowserState, BrowserState], None]] = []
        self._game_detection_callbacks: List[Callable[[GameSession], None]] = []

    async def initialize(self) -> None:
        """Initialize the browser controller"""
        # Load bookmarks if available
        await self._load_bookmarks()

    async def shutdown(self) -> None:
        """Shutdown the browser controller"""
        # Save bookmarks
        await self._save_bookmarks()

    async def _load_bookmarks(self) -> None:
        """Load bookmarks from storage"""
        bookmarks_path = Path.home() / ".angela_ai" / "browser_bookmarks.json"
        try:
            if bookmarks_path.exists():
                import json as _json
                data = _json.loads(await async_read_text(bookmarks_path))
                self.bookmarks = {
                    bid: Bookmark(**bd) for bid, bd in data.items()
                }
                logger.info(f"Loaded {len(self.bookmarks)} bookmarks")
        except Exception as e:
            logger.warning(f"Failed to load bookmarks: {e}")

    async def _save_bookmarks(self) -> None:
        """Save bookmarks to storage"""
        bookmarks_path = Path.home() / ".angela_ai" / "browser_bookmarks.json"
        try:
            bookmarks_path.parent.mkdir(parents=True, exist_ok=True)
            import json as _json
            data = {bid: bd.__dict__ for bid, bd in self.bookmarks.items()}
            await async_write_text(bookmarks_path, _json.dumps(data, indent=2, default=str))
            logger.info(f"Saved {len(self.bookmarks)} bookmarks")
        except Exception as e:
            logger.warning(f"Failed to save bookmarks: {e}")

    def _set_state(self, new_state: BrowserState) -> None:
        """Set browser state with notifications"""
        if new_state != self.current_state:
            old_state = self.current_state
            self.current_state = new_state

            for callback in self._state_change_callbacks:
                try:
                    callback(old_state, new_state)
                except Exception as e:  # broad exception acceptable: callback errors should not break state changes
                    logger.error(f"Error in {__name__}: {e}", exc_info=True)

    async def search(
        self, query: str, engine: Optional[SearchEngine] = None, max_results: int = 10
    ) -> List[SearchResult]:
        """
        Perform web search

        Args:
            query: Search query
            engine: Search engine to use (default if None)
            max_results: Maximum results to return

        Returns:
            List of search results
        """
        self._set_state(BrowserState.NAVIGATING)

        search_engine = engine or self.default_engine

        try:
            results = await self._perform_real_search(query, search_engine, max_results)

            self.active_search_results = results

            # Record history
            self.search_history.append(
                {
                    "query": query,
                    "engine": search_engine.search_name,
                    "timestamp": datetime.now(),
                    "result_count": len(results),
                }
            )

            self._set_state(BrowserState.IDLE)
            return results

        except Exception as e:  # broad exception acceptable: search should be resilient to errors
            logger.error(f"Error in {__name__}: {e}", exc_info=True)
            self._set_state(BrowserState.IDLE)

            return []

    async def _perform_real_search(
        self, query: str, engine: SearchEngine, max_results: int
    ) -> List[SearchResult]:
        """
        [Phase 18.1] 執行真實網路搜尋 (使用 DuckDuckGo HTML 版)
        取代原有的 _perform_mock_search 佔位符。
        """
        results = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        url = "https://html.duckduckgo.com/html/"
        data = {"q": query}

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(url, data=data, timeout=timeout_value("http_post", 10.0)) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")
                        
                        # 解析 DuckDuckGo 結果
                        for result_div in soup.find_all("div", class_="result__body", limit=max_results):
                            title_a = result_div.find("a", class_="result__title")
                            snippet_a = result_div.find("a", class_="result__snippet")
                            result_div.find("a", class_="result__url")
                            
                            if title_a and snippet_a:
                                title = title_a.get_text(strip=True)
                                link = title_a.get("href", "")
                                snippet = snippet_a.get_text(strip=True)
                                
                                results.append(
                                    SearchResult(
                                        title=title,
                                        url=link,
                                        snippet=snippet,
                                        relevance_score=1.0 - (len(results) * 0.1),
                                        source_engine="DuckDuckGo"
                                    )
                                )
        except Exception as e:  # broad exception acceptable: real search should be resilient to network errors
            logger.error(f"Real search failed: {e}", exc_info=True)
            
        return results

    async def extract_content(self, url: str) -> Optional[ExtractedContent]:
        """
        Extract content from a webpage

        Args:
            url: URL to extract content from

        Returns:
            Extracted content or None if failed
        """
        self._set_state(BrowserState.LOADING)

        try:
            content = await self._perform_real_extraction(url)

            self._set_state(BrowserState.IDLE)
            return content

        except Exception as e:  # broad exception acceptable: content extraction should be resilient to errors
            logger.error(f"Error in {__name__}: {e}", exc_info=True)
            self._set_state(BrowserState.IDLE)

            return None

    async def _perform_real_extraction(self, url: str) -> Optional[ExtractedContent]:
        """
        [Phase 18.2] 執行真實網頁內容擷取
        取代原有的 _perform_mock_extraction 佔位符。
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=timeout_value("http_get", 15.0)) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")
                        
                        # 移除 script 與 style
                        for script in soup(["script", "style", "nav", "footer", "header"]):
                            script.extract()
                            
                        # 取得純文字
                        text = soup.get_text(separator="\n", strip=True)
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        clean_text = "\n".join(chunk for chunk in chunks if chunk)
                        
                        # 提取圖片與連結 (前幾個)
                        images = [img.get('src') for img in soup.find_all('img') if img.get('src')][:5]
                        links = [a.get('href') for a in soup.find_all('a', href=True)][:5]
                        
                        title = soup.title.string if soup.title else "Untitled"
                        
                        return ExtractedContent(
                            url=url,
                            title=title.strip(),
                            text_content=clean_text[:5000], # 限制長度避免過大
                            images=images,
                            links=links,
                            word_count=len(clean_text.split()),
                            summary=clean_text[:200] + "..." if len(clean_text) > 200 else clean_text
                        )
                    else:
                        logger.warning(f"Extraction failed with status {response.status} for {url}", exc_info=True)
                        return None
        except Exception as e:  # broad exception acceptable: real extraction should be resilient to network errors
            logger.error(f"Real extraction failed: {e}", exc_info=True)
            return None

    def detect_game(self, url: str, page_title: str, page_content: str) -> bool:
        """
        Detect if current page is a game

        Args:
            url: Page URL
            page_title: Page title
            page_content: Page content

        Returns:
            True if game detected
        """
        # Check for game keywords in URL and title
        combined_text = f"{url} {page_title} {page_content[:500]}".lower()

        for keyword in self.game_keywords:
            if keyword in combined_text:
                # Start game session
                if not self.current_game or not self.current_game.is_active:
                    self.current_game = GameSession(
                        game_name=page_title[:50], game_url=url, is_active=True
                    )
                    self.game_sessions.append(self.current_game)

                    # Notify callbacks
                    for callback in self._game_detection_callbacks:
                        try:
                            callback(self.current_game)
                        except Exception as e:  # broad exception acceptable: callback errors should not break game detection
                            logger.error(f"Error in {__name__}: {e}", exc_info=True)

                self._set_state(BrowserState.PLAYING_GAME)
                return True

        return False

    def end_game_session(self) -> None:
        """End current game session"""
        if self.current_game and self.current_game.is_active:
            self.current_game.is_active = False
            self.current_game.end_time = datetime.now()

            # Calculate duration
            duration = self.current_game.end_time - self.current_game.start_time
            self.current_game.duration_minutes = duration.total_seconds() / 60.0

            self.current_game = None
            self._set_state(BrowserState.IDLE)

    def is_playing_game(self) -> bool:
        """Check if currently playing a game"""
        return self.current_state == BrowserState.PLAYING_GAME and self.current_game is not None

    def get_active_game(self) -> Optional[GameSession]:
        """Get currently active game session"""
        return self.current_game if self.is_playing_game() else None

    def add_bookmark(
        self,
        title: str,
        url: str,
        category: str = "未分类",
        tags: Optional[List[str]] = None,
        notes: str = "",
    ) -> Bookmark:
        """
        Add a new bookmark

        Args:
            title: Bookmark title
            url: Bookmark URL
            category: Bookmark category
            tags: List of tags
            notes: Notes about the bookmark

        Returns:
            Created bookmark
        """
        bookmark_id = f"bm_{datetime.now().timestamp()}"

        bookmark = Bookmark(
            bookmark_id=bookmark_id,
            title=title,
            url=url,
            category=category,
            tags=tags or [],
            notes=notes,
        )

        self.bookmarks[bookmark_id] = bookmark
        return bookmark

    def remove_bookmark(self, bookmark_id: str) -> bool:
        """Remove a bookmark"""
        if bookmark_id in self.bookmarks:
            del self.bookmarks[bookmark_id]
            return True
        return False

    def get_bookmarks(
        self, category: Optional[str] = None, tag: Optional[str] = None
    ) -> List[Bookmark]:
        """
        Get bookmarks with optional filtering

        Args:
            category: Filter by category
            tag: Filter by tag

        Returns:
            List of matching bookmarks
        """
        bookmarks = list(self.bookmarks.values())

        if category:
            bookmarks = [b for b in bookmarks if b.category == category]

        if tag:
            bookmarks = [b for b in bookmarks if tag in b.tags]

        return bookmarks

    def search_bookmarks(self, query: str) -> List[Bookmark]:
        """Search bookmarks by query"""
        query_lower = query.lower()
        results = []

        for bookmark in self.bookmarks.values():
            if (
                query_lower in bookmark.title.lower()
                or query_lower in bookmark.url.lower()
                or query_lower in bookmark.notes.lower()
                or any(query_lower in tag.lower() for tag in bookmark.tags)
            ):
                results.append(bookmark)

        return results

    def record_bookmark_visit(self, bookmark_id: str) -> None:
        """Record a visit to a bookmark"""
        if bookmark_id in self.bookmarks:
            bookmark = self.bookmarks[bookmark_id]
            bookmark.visit_count += 1
            bookmark.last_visited = datetime.now()

    def get_bookmark_categories(self) -> List[str]:
        """Get all bookmark categories"""
        categories = set(b.category for b in self.bookmarks.values())
        return sorted(list(categories))

    def get_popular_bookmarks(self, limit: int = 10) -> List[Bookmark]:
        """Get most visited bookmarks"""
        sorted_bookmarks = sorted(
            self.bookmarks.values(), key=lambda b: b.visit_count, reverse=True
        )
        return sorted_bookmarks[:limit]

    def get_recent_bookmarks(self, limit: int = 10) -> List[Bookmark]:
        """Get recently added bookmarks"""
        sorted_bookmarks = sorted(self.bookmarks.values(), key=lambda b: b.created_at, reverse=True)
        return sorted_bookmarks[:limit]

    def register_state_change_callback(
        self, callback: Callable[[BrowserState, BrowserState], None]
    ) -> None:
        """Register callback for state changes"""
        self._state_change_callbacks.append(callback)

    def register_game_detection_callback(self, callback: Callable[[GameSession], None]) -> None:
        """Register callback for game detection"""
        self._game_detection_callbacks.append(callback)

    def get_game_statistics(self) -> Dict[str, Any]:
        """Get game play statistics"""
        total_sessions = len(self.game_sessions)
        total_minutes = sum(s.duration_minutes for s in self.game_sessions if not s.is_active)

        game_counts: Dict[str, int] = {}
        for session in self.game_sessions:
            game_counts[session.game_name] = game_counts.get(session.game_name, 0) + 1

        return {
            "total_sessions": total_sessions,
            "total_hours": total_minutes / 60.0,
            "currently_playing": self.is_playing_game(),
            "favorite_games": sorted(game_counts.items(), key=lambda x: x[1], reverse=True)[:5],
        }

    def get_search_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get search history"""
        return self.search_history[-limit:]


# Example usage
if __name__ == "__main__":

    async def demo() -> None:
        """Run a demonstration."""
        browser = BrowserController()
        await browser.initialize()

        logger.info("=" * 60)
        logger.info("Angela AI v6.0 - 浏览器控制器演示")
        logger.info("Browser Controller Demo")
        logger.info("=" * 60)

        # Search
        logger.info("\n搜索演示 / Search demo:")
        results = await browser.search("machine learning tutorial", max_results=3)
        logger.info(f"  找到 {len(results)} 个结果")
        for i, result in enumerate(results, 1):
            logger.info(f"  {i}. {result.title}")
            logger.info(f"     {result.url}")

        # Add bookmark
        logger.info("\n书签管理 / Bookmark management:")
        bookmark = browser.add_bookmark(
            title="Machine Learning Tutorial",
            url="https://example.com/ml-tutorial",
            category="学习",
            tags=["machine learning", "tutorial", "AI"],
            notes="Great tutorial for beginners",
        )
        logger.info(f"  已添加书签: {bookmark.title}")
        logger.info(f"  ID: {bookmark.bookmark_id}")

        # List bookmarks
        all_bookmarks = browser.get_bookmarks()
        logger.info(f"  总书签数: {len(all_bookmarks)}")

        # Game detection
        logger.info("\n游戏检测 / Game detection:")
        is_game = browser.detect_game(
            url="https://example-game.com/play",
            page_title="Awesome Game - Play Now!",
            page_content="Welcome to the best online game experience...",
        )
        logger.info(f"  游戏检测: {is_game}")
        active_game = browser.get_active_game()
        if active_game:
            logger.info(f"  当前游戏: {active_game.game_name}")

        # Statistics
        logger.info("\n统计信息 / Statistics:")
        stats = browser.get_game_statistics()
        logger.info(f"  游戏会话数: {stats['total_sessions']}")

        await browser.shutdown()
        logger.info("\n系统已关闭 / System shutdown complete")

    asyncio.run(demo())
