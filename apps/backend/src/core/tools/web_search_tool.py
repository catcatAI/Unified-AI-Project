"""
网络搜索工具
"""

import os
from typing import Optional, Dict, Any, List

# 尝试导入requests和beautifulsoup4
try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# 尝试导入yaml
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class WebSearchTool:
    """网络搜索工具"""

    def __init__(self):
        """初始化"""
        # 使用硬编码配置，避免配置文件依赖
        self.search_url_template = "https://duckduckgo.com/html/?q={query}"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'configs',
            'system_config.yaml'
        )

        if YAML_AVAILABLE and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    all_configs = yaml.safe_load(f)
                    return all_configs.get('web_search_tool', {})
            except Exception as e:
                print(f"配置文件加载失败，使用默认值: {e}")

        return {}

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        执行网络搜索

        Args:
            query: 搜索查询
            num_results: 返回结果数量

        Returns:
            搜索结果列表
        """
        if not REQUESTS_AVAILABLE:
            return [{"error": "requests库不可用"}]

        try:
            url = self.search_url_template.format(query=query)
            headers = {"User-Agent": self.user_agent}

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            # 简化实现：解析搜索结果
            for result in soup.find_all('a', class_='result__a', limit=num_results):
                results.append({
                    "title": result.get_text(strip=True),
                    "url": result.get('href', '')
                })

            return results

        except Exception as e:
            return [{"error": str(e)}]