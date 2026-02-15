"""
CSV工具 - 用于CSV数据分析
"""

from typing import Dict, Any, Optional
import logging
logger = logging.getLogger(__name__)

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class CsvTool:
    """CSV分析工具"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化CsvTool"""
        self.config = config or {}
        logger.info(f"{self.__class__.__name__} initialized.")

    def analyze(self, csv_content: str, query: str) -> Dict[str, Any]:
        """
        分析CSV数据

        Args:
            csv_content: CSV文件内容
            query: 分析查询

        Returns:
            分析结果
        """
        if not PANDAS_AVAILABLE:
            return {"status": "failure", "error": "pandas not available"}

        from io import StringIO

        try:
            df = pd.read_csv(StringIO(csv_content))
            query = query.lower().strip()

            if "summarize" in query:
                return {"status": "success", "result": df.describe().to_string()}
            elif "columns" in query:
                return {"status": "success", "result": ", ".join(df.columns.tolist())}
            elif "shape" in query:
                return {"status": "success", "result": f"Rows: {df.shape[0]}, Columns: {df.shape[1]}"}
            else:
                return {"status": "failure", "error": f"Unsupported query: '{query}'. Try 'summarize', 'columns', or 'shape'."}

        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            return {"status": "failure", "error": str(e)}
