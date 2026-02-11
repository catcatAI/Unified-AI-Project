"""CSV工具"""

from typing import Dict, Any, Optional


class CsvTool:
    """CSV数据分析工具"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化"""
        self.config = config or {}
        print(f"{self.__class__.__name__} initialized.")

    def analyze(self, csv_content: str, query: str) -> Dict[str, Any]:
        """
        分析CSV数据

        Args:
            csv_content: CSV文件内容
            query: 分析查询

        Returns:
            分析结果
        """
        from io import StringIO

        try:
            # 简化实现：不使用pandas
            lines = csv_content.strip().split('\n')

            if not lines:
                return {"status": "failure", "error": "Empty CSV content"}

            headers = lines[0].split(',')
            row_count = len(lines) - 1

            query_lower = query.lower().strip()

            if "columns" in query_lower:
                return {"status": "success", "result": ", ".join(headers)}
            elif "shape" in query_lower:
                return {"status": "success", "result": f"Rows: {row_count}, Columns: {len(headers)}"}
            elif "summarize" in query_lower:
                return {"status": "success", "result": f"CSV with {row_count} rows and {len(headers)} columns"}
            else:
                return {"status": "failure", "error": f"Unsupported query: '{query}'. Try 'summarize', 'columns', or 'shape'."}

        except Exception as e:
            return {"status": "failure", "error": str(e)}