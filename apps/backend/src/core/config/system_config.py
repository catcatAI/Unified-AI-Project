"""
系统配置模块
"""

import os
from typing import Dict, Any

def get_system_config() -> Dict[str, Any]:
    """获取系统配置"""
    return {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "debug": os.getenv("DEBUG", "true").lower() == "true",
        "host": os.getenv("HOST", "0.0.0.0"),
        "port": int(os.getenv("PORT", "8000")),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        
        # AI运维系统配置
        "ai_ops": {
            "enabled": os.getenv("AI_OPS_ENABLED", "true").lower() == "true",
            "redis_host": os.getenv("REDIS_HOST", "localhost"),
            "redis_port": int(os.getenv("REDIS_PORT", "6379")),
            "redis_db": int(os.getenv("REDIS_DB", "0")),
            "monitoring_interval": int(os.getenv("MONITORING_INTERVAL", "300")),  # 秒
            "anomaly_threshold": float(os.getenv("ANOMALY_THRESHOLD", "0.1")),
            "prediction_window": int(os.getenv("PREDICTION_WINDOW", "24")),  # 小时
            "min_data_points": int(os.getenv("MIN_DATA_POINTS", "100")),
            "auto_healing": os.getenv("AUTO_HEALING", "true").lower() == "true",
            "performance_monitoring": os.getenv("PERFORMANCE_MONITORING", "true").lower() == "true"
        },
        
        # HSP协议配置
        "hsp": {
            "enabled": os.getenv("HSP_ENABLED", "true").lower() == "true",
            "mqtt_broker": os.getenv("MQTT_BROKER", "localhost"),
            "mqtt_port": int(os.getenv("MQTT_PORT", "1883")),
            "mqtt_username": os.getenv("MQTT_USERNAME", ""),
            "mqtt_password": os.getenv("MQTT_PASSWORD", ""),
            "keepalive": int(os.getenv("MQTT_KEEPALIVE", "60"))
        },
        
        # 记忆系统配置
        "memory": {
            "chroma_host": os.getenv("CHROMA_HOST", "localhost"),
            "chroma_port": int(os.getenv("CHROMA_PORT", "8000")),
            "vector_dimension": int(os.getenv("VECTOR_DIMENSION", "384")),
            "max_memory_size": int(os.getenv("MAX_MEMORY_SIZE", "10000"))
        },
        
        # 训练系统配置
        "training": {
            "auto_training": os.getenv("AUTO_TRAINING", "true").lower() == "true",
            "model_path": os.getenv("MODEL_PATH", "./models"),
            "data_path": os.getenv("DATA_PATH", "./data"),
            "checkpoint_interval": int(os.getenv("CHECKPOINT_INTERVAL", "100")),
            "batch_size": int(os.getenv("BATCH_SIZE", "32"))
        }
    }

def get_ai_ops_config() -> Dict[str, Any]:
    """获取AI运维系统专用配置"""
    config = get_system_config()["ai_ops"]
    return config

def get_hsp_config() -> Dict[str, Any]:
    """获取HSP协议配置"""
    config = get_system_config()["hsp"]
    return config

def get_memory_config() -> Dict[str, Any]:
    """获取记忆系统配置"""
    config = get_system_config()["memory"]
    return config

def get_training_config() -> Dict[str, Any]:
    """获取训练系统专用配置"""
    config = get_system_config()["training"]
    return config