import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import pytest
import asyncio

@pytest.mark.asyncio
async def test_simple_async():
    """简单的异步测试，用于验证测试环境是否正常工作"""
    await asyncio.sleep(0.1)
    assert True

def test_simple_sync():
    """简单的同步测试，用于验证测试环境是否正常工作"""
    assert True