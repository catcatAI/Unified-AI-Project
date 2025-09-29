#!/usr/bin/env python3
"""
统一日志记录工具
"""

import logging
import sys
from pathlib import Path


class UnifiedLogger:
    def __init__(self, name="unified-ai", level=logging.INFO) -> None:
        self.logger = logging.getLogger(name)
        _ = self.logger.setLevel(level)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            # 创建控制台处理器
            console_handler = logging.StreamHandler(sys.stdout)
            _ = console_handler.setLevel(level)
            
            # 创建文件处理器
            log_dir = Path(__file__).parent.parent.parent / "logs"
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / "unified-ai.log"
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            _ = file_handler.setLevel(level)
            
            # 创建格式器
            formatter = logging.Formatter(
                _ = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            _ = console_handler.setFormatter(formatter)
            _ = file_handler.setFormatter(formatter)
            
            # 添加处理器
            _ = self.logger.addHandler(console_handler)
            _ = self.logger.addHandler(file_handler)
    
    def debug(self, message):
        _ = self.logger.debug(message)
    
    def info(self, message):
        _ = self.logger.info(message)
    
    def warning(self, message):
        _ = self.logger.warning(message)
    
    def error(self, message):
        _ = self.logger.error(message)
    
    def critical(self, message):
        _ = self.logger.critical(message)
    
    def set_level(self, level):
        """设置日志级别"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        numeric_level = level_map.get(level.upper(), logging.INFO)
        _ = self.logger.setLevel(numeric_level)
        
        for handler in self.logger.handlers:
            _ = handler.setLevel(numeric_level)
    
    def get_level(self):
        """获取当前日志级别"""
        level_map = {
            logging.DEBUG: 'DEBUG',
            logging.INFO: 'INFO',
            logging.WARNING: 'WARNING',
            logging.ERROR: 'ERROR',
            logging.CRITICAL: 'CRITICAL'
        }
        return level_map.get(self.logger.level, 'INFO')


# 创建全局日志记录器实例
_logger = UnifiedLogger()


def debug(message):
    _logger.debug(message)


def info(message):
    _logger.info(message)


def warning(message):
    _logger.warning(message)


def error(message):
    _logger.error(message)


def critical(message):
    _logger.critical(message)


def set_level(level):
    _logger.set_level(level)


def get_level():
    return _logger.get_level()