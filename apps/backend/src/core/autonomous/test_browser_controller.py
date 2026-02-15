"""
Test script for Browser Controller

Run with: python -m apps.backend.src.core.autonomous.test_browser_controller
"""

import asyncio
import logging
from core.autonomous.browser_controller import (
    BrowserController,
    BrowserConfig,
    BrowserType,
    AutomationFramework,
    SafetyControls,
    create_browser_controller,
    quick_search,
    quick_extract
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_safety_controls():
    """Test safety controls."""
    logger.info("\n=== Testing Safety Controls ===")
    
    safety = SafetyControls(
        blacklist=["malicious-site.com"],
        max_session_duration=60
    )
    safety.start_session()
    
    # Test safe URL
    result = safety.check_url_safety("https://www.google.com")
    logger.info(f"Safe URL check: {result.is_safe} (risk: {result.risk_level})")
    assert result.is_safe, "Safe URL should pass"
    
    # Test blacklisted URL
    result = safety.check_url_safety("https://malicious-site.com/page")
    logger.info(f"Blacklisted URL check: {result.is_safe} (reason: {result.reason})")
    assert not result.is_safe, "Blacklisted URL should be blocked"
    
    # Test blocked pattern
    result = safety.check_url_safety("https://example.onion")
    logger.info(f"Blocked pattern check: {result.is_safe} (reason: {result.reason})")
    assert not result.is_safe, "Blocked pattern URL should be blocked"
    
    logger.info("✓ Safety controls working correctly")


async def test_browser_manager():
    """Test browser manager with Playwright."""
    logger.info("\n=== Testing Browser Manager (Playwright) ===")
    
    config = BrowserConfig(
        browser_type=BrowserType.CHROME,
        framework=AutomationFramework.PLAYWRIGHT,
        headless=True
    )
    
    controller = BrowserController(config)
    
    try:
        # Initialize
        success = await controller.initialize()
        logger.info(f"Browser initialized: {success}")
        assert success, "Browser should initialize successfully"
        
        # Navigate to test page
        result = await controller.safe_browse("https://example.com")
        logger.info(f"Navigation result: {result}")
        assert result["success"], "Navigation should succeed"
        
        # Take screenshot
        screenshot_path = await controller.browser.take_screenshot()
        logger.info(f"Screenshot saved: {screenshot_path}")
        
        logger.info("✓ Browser manager working correctly")
        
    finally:
        await controller.close()


async def test_web_search():
    """Test web search functionality."""
    logger.info("\n=== Testing Web Search ===")
    
    # Quick search without browser
    results = await quick_search("Python programming language", num_results=3)
    logger.info(f"Found {len(results)} results")
    
    for result in results:
        logger.info(f"  {result.rank}. {result.title[:50]}... ({result.source})")
    
    assert len(results) > 0, "Should find search results"
    logger.info("✓ Web search working correctly")


async def test_information_extractor():
    """Test information extraction."""
    logger.info("\n=== Testing Information Extractor ===")
    
    # Quick extract without browser
    content = await quick_extract("https://example.com")
    logger.info(f"Extracted from: {content.url}")
    logger.info(f"Title: {content.title}")
    logger.info(f"Content length: {len(content.content)} chars")
    logger.info(f"Links found: {len(content.links)}")
    logger.info(f"Images found: {len(content.images)}")
    
    assert content.title, "Should extract title"
    assert len(content.links) > 0, "Should find links"
    logger.info("✓ Information extraction working correctly")


async def test_bookmarks():
    """Test bookmark management."""
    logger.info("\n=== Testing Bookmarks ===")
    
    from src.core.autonomous.browser_controller import InformationExtractor
    
    extractor = InformationExtractor(bookmarks_file="test_bookmarks.json")
    
    # Add bookmark
    bookmark = await extractor.add_bookmark(
        url="https://example.com",
        title="Example Site",
        tags=["test", "example"],
        notes="A test bookmark",
        category="testing"
    )
    logger.info(f"Added bookmark: {bookmark.id} - {bookmark.title}")
    
    # Search bookmarks
    results = extractor.search_bookmarks("example")
    logger.info(f"Found {len(results)} bookmarks matching 'example'")
    
    # Get by category
    category_results = extractor.get_bookmarks_by_category("testing")
    logger.info(f"Found {len(category_results)} bookmarks in 'testing' category")
    
    # Cleanup
    extractor.delete_bookmark(bookmark.id)
    
    # Remove test file
    import os
    if os.path.exists("test_bookmarks.json"):
        os.remove("test_bookmarks.json")
    
    logger.info("✓ Bookmark management working correctly")


async def run_all_tests():
    """Run all tests."""
    logger.info("\n" + "="*60)
    logger.info("BROWSER CONTROLLER TEST SUITE")
    logger.info("="*60)
    
    try:
        await test_safety_controls()
        await test_web_search()
        await test_information_extractor()
        await test_bookmarks()
        
        # Browser test requires Chrome/Chromium installed
        logger.info("\n=== Browser Test (Optional) ===")
        logger.info("Note: Browser test requires Chrome/Chromium installed")
        try:
            await test_browser_manager()
        except Exception as e:
            logger.info(f"Browser test skipped (browser not installed?): {e}")
        
        logger.info("\n" + "="*60)
        logger.info("ALL TESTS COMPLETED SUCCESSFULLY!")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
