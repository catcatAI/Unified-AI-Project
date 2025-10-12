"""
API路由模块
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    """根路径"""
    return {"message": "Unified AI Project API"}

@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}