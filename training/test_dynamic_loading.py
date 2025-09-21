#!/usr/bin/env python3
"""
动态载入功能测试
测试100MB动态载入切分方案的实现
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
backend_path = project_root / "apps" / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_file_chunking():
    """测试文件分块功能"""
    logger.info("开始测试文件分块功能...")
    
    try:
        from training.dynamic_loader import FileChunker
        
        # 创建测试文件
        test_file = "test_chunking_file.bin"
        file_size = 250 * 1024 * 1024  # 250MB
        
        logger.info(f"创建 {file_size} 字节的测试文件...")
        with open(test_file, "wb") as f:
            f.write(os.urandom(file_size))
        
        # 测试文件分块
        chunker = FileChunker()
        chunks = chunker.chunk_file(test_file)
        
        # 验证分块结果
        expected_chunks = 3  # 250MB文件应该被切分为3个块（100MB + 100MB + 50MB）
        if len(chunks) != expected_chunks:
            logger.error(f"分块数量不正确，期望: {expected_chunks}，实际: {len(chunks)}")
            return False
        
        # 验证块大小
        expected_sizes = [100*1024*1024, 100*1024*1024, 50*1024*1024]
        for i, chunk in enumerate(chunks):
            if chunk['size'] != expected_sizes[i]:
                logger.error(f"块 {i} 大小不正确，期望: {expected_sizes[i]}，实际: {chunk['size']}")
                return False
        
        logger.info(f"文件分块测试通过，共 {len(chunks)} 个块")
        
        # 清理测试文件
        os.remove(test_file)
        return True
        
    except Exception as e:
        logger.error(f"文件分块测试失败: {e}")
        return False


def test_memory_mapping():
    """测试内存映射功能"""
    logger.info("开始测试内存映射功能...")
    
    try:
        from training.dynamic_loader import MemoryMappedFile, FileChunker
        
        # 创建测试文件
        test_file = "test_mapping_file.bin"
        file_size = 150 * 1024 * 1024  # 150MB
        
        logger.info(f"创建 {file_size} 字节的测试文件...")
        with open(test_file, "wb") as f:
            test_data = os.urandom(file_size)
            f.write(test_data)
        
        # 测试整个文件映射
        logger.info("测试整个文件映射...")
        with MemoryMappedFile(test_file) as mapped_file:
            # 读取前100字节
            data = mapped_file.read(100)
            if len(data) != 100:
                logger.error(f"读取数据大小不正确，期望: 100，实际: {len(data)}")
                return False
            
            # 验证数据正确性
            if data != test_data[:100]:
                logger.error("读取的数据不正确")
                return False
        
        # 测试块映射
        logger.info("测试块映射...")
        chunker = FileChunker()
        chunks = chunker.chunk_file(test_file)
        
        # 映射第一个块
        with MemoryMappedFile(test_file, chunks[0]) as mapped_file:
            # 读取块的所有数据
            data = mapped_file.read()
            if len(data) != chunks[0]['size']:
                logger.error(f"读取块数据大小不正确，期望: {chunks[0]['size']}，实际: {len(data)}")
                return False
            
            # 验证数据正确性
            start = chunks[0]['start']
            end = chunks[0]['end']
            if data != test_data[start:end]:
                logger.error("读取的块数据不正确")
                return False
        
        logger.info("内存映射测试通过")
        
        # 清理测试文件
        os.remove(test_file)
        return True
        
    except Exception as e:
        logger.error(f"内存映射测试失败: {e}")
        return False


def test_lru_cache():
    """测试LRU缓存功能"""
    logger.info("开始测试LRU缓存功能...")
    
    try:
        from training.dynamic_loader import LRUCache
        
        # 创建缓存实例
        cache = LRUCache(max_size=3)
        
        # 测试添加和获取
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # 验证获取
        if cache.get("key1") != "value1":
            logger.error("缓存获取失败")
            return False
        
        if cache.get("key2") != "value2":
            logger.error("缓存获取失败")
            return False
        
        # 添加第四个项，应该移除最久未使用的项（key1）
        cache.put("key4", "value4")
        
        # 验证key1已被移除
        if cache.get("key1") is not None:
            logger.error("LRU淘汰机制失败")
            return False
        
        # 验证其他项仍然存在
        if cache.get("key2") != "value2":
            logger.error("缓存项意外被移除")
            return False
        
        if cache.get("key3") != "value3":
            logger.error("缓存项意外被移除")
            return False
        
        if cache.get("key4") != "value4":
            logger.error("缓存项添加失败")
            return False
        
        # 测试更新现有项
        cache.put("key2", "updated_value2")
        if cache.get("key2") != "updated_value2":
            logger.error("缓存项更新失败")
            return False
        
        logger.info("LRU缓存测试通过")
        return True
        
    except Exception as e:
        logger.error(f"LRU缓存测试失败: {e}")
        return False


def test_dynamic_loader():
    """测试动态载入器主功能"""
    logger.info("开始测试动态载入器主功能...")
    
    try:
        from training.dynamic_loader import DynamicLoader
        
        # 创建测试文件
        test_file = "test_loader_file.bin"
        file_size = 250 * 1024 * 1024  # 250MB
        
        logger.info(f"创建 {file_size} 字节的测试文件...")
        with open(test_file, "wb") as f:
            test_data = os.urandom(file_size)
            f.write(test_data)
        
        # 创建动态载入器
        loader = DynamicLoader(chunk_size=100*1024*1024, cache_size=5)
        
        # 获取文件块信息
        chunks = loader.get_file_chunk_info(test_file)
        expected_chunks = 3
        if len(chunks) != expected_chunks:
            logger.error(f"文件块信息不正确，期望: {expected_chunks}，实际: {len(chunks)}")
            return False
        
        # 加载第一个块
        data1 = loader.load_file_chunk(test_file, 0)
        expected_size = 100 * 1024 * 1024
        if len(data1) != expected_size:
            logger.error(f"加载的第一个块大小不正确，期望: {expected_size}，实际: {len(data1)}")
            return False
        
        # 验证数据正确性
        if data1 != test_data[:expected_size]:
            logger.error("加载的第一个块数据不正确")
            return False
        
        # 再次加载第一个块（应该从缓存获取）
        data2 = loader.load_file_chunk(test_file, 0)
        if data2 != data1:
            logger.error("缓存功能未正常工作")
            return False
        
        # 加载第二个块
        data3 = loader.load_file_chunk(test_file, 1)
        expected_size = 100 * 1024 * 1024
        if len(data3) != expected_size:
            logger.error(f"加载的第二个块大小不正确，期望: {expected_size}，实际: {len(data3)}")
            return False
        
        # 验证数据正确性
        start = 100 * 1024 * 1024
        end = 200 * 1024 * 1024
        if data3 != test_data[start:end]:
            logger.error("加载的第二个块数据不正确")
            return False
        
        # 获取缓存统计信息
        stats = loader.get_cache_stats()
        if stats['current_size'] != 2:  # 应该缓存了2个块
            logger.error(f"缓存大小不正确，期望: 2，实际: {stats['current_size']}")
            return False
        
        logger.info("动态载入器主功能测试通过")
        
        # 清理测试文件
        os.remove(test_file)
        return True
        
    except Exception as e:
        logger.error(f"动态载入器主功能测试失败: {e}")
        return False


def main():
    """主测试函数"""
    logger.info("开始动态载入功能测试")
    
    # 运行所有测试
    tests = [
        ("文件分块测试", test_file_chunking),
        ("内存映射测试", test_memory_mapping),
        ("LRU缓存测试", test_lru_cache),
        ("动态载入器主功能测试", test_dynamic_loader)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            logger.info(f"运行 {test_name}...")
            result = test_func()
            if result:
                logger.info(f"✅ {test_name} 通过")
                passed += 1
            else:
                logger.error(f"❌ {test_name} 失败")
                failed += 1
        except Exception as e:
            logger.error(f"❌ {test_name} 发生异常: {e}")
            failed += 1
    
    # 输出测试结果摘要
    logger.info("=" * 50)
    logger.info("测试结果摘要:")
    logger.info(f"  通过: {passed}")
    logger.info(f"  失败: {failed}")
    logger.info(f"  总计: {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 所有测试通过!")
        return True
    else:
        logger.error(f"❌ {failed} 个测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)