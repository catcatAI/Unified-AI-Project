"""
Angela Knowledge Graph - 代碼結構知識圖譜
==========================================

純演算法構建，不依賴 LLM。
將代碼庫結構轉化為可查詢的圖譜。

節點類型：
  - FileNode: 文件
  - ClassNode: 類
  - FunctionNode: 函數
  - MethodNode: 方法
  - ImportNode: import 語句

邊類型：
  - CONTAINS: 文件包含類/函數
  - IMPORTS: 文件導入模組
  - CALLS: 函數調用其他函數
  - INHERITS: 類繼承關係
  - DECORATED_BY: 函數被裝飾器標記

Author: Angela AI Development Team
Version: 6.2.1
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

from __future__ import annotations
