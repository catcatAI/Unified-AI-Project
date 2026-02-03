# Path Configuration (路徑設定)

## 總覽 (Overview)

`path_config.py` 模組是整個 Unified AI 專案中用於路徑管理的中央樞紐。它的主要目標是統一管理所有重要的檔案和目錄路徑，以避免在程式碼中硬編碼路徑字串，並透過使用 `pathlib` 模組確保在 Windows, macOS, 和 Linux 等不同作業系統上的相容性。

## 主要特性 (Key Features)

- **集中管理**: 所有關鍵目錄的路徑都在此模組中定義，方便統一修改與維護。
- **根目錄相對**: 所有路徑都基於一個動態計算出的專案根目錄 (`PROJECT_ROOT`)，使得專案可以被移動到任何位置而無需修改路徑設定。
- **跨平台相容**: 使用 `pathlib.Path` 物件來處理路徑，自動適應不同作業系統的路徑分隔符（例如 `\` 或 `/`）。
- **目錄自動建立**: 當此模組被首次匯入時，它會自動檢查並建立所有預定義的關鍵目錄，防止因目錄不存在而導致的 `FileNotFoundError`。

## 核心定義 (Core Definitions)

### 路徑常數 (Path Constants)

以下是模組中定義的核心路徑常數：

- `PROJECT_ROOT`: 專案的絕對根目錄路徑。
- `DATA_DIR`: 用於存放資料集和其他原始資料。
- `TRAINING_DIR`: 包含所有與模型訓練相關的檔案。
- `MODELS_DIR`: 用於儲存訓練完成的模型檔案。
- `CHECKPOINTS_DIR`: 用於儲存訓練過程中的檢查點。
- `CONFIGS_DIR`: 用於存放訓練設定檔。

### 輔助函式 (Helper Functions)

- `get_data_path(dataset_name: str) -> Path`:
  傳入資料集名稱，返回其在 `DATA_DIR` 中的完整路徑。

- `get_training_config_path(config_name: str) -> Path`:
  傳入設定檔名稱，返回其在 `CONFIGS_DIR` 中的完整路徑。

- `resolve_path(path_str: str) -> Path`:
  一個通用的路徑解析工具。如果輸入的字串是絕對路徑，則直接返回；如果是相對路徑，則將其與 `PROJECT_ROOT` 結合，返回一個絕對路徑。

## 使用範例 (Usage Example)

在專案的其他模組中，可以這樣使用 `path_config`：

```python
# 從 path_config 匯入所需的變數和函式
from apps.backend.src.path_config import get_data_path, MODELS_DIR, resolve_path

# 獲取特定資料集的路徑
user_data_path = get_data_path("user_profiles.csv")
print(f"從此路徑載入資料: {user_data_path}")

# 定義一個新模型的儲存路徑
new_model_path = MODELS_DIR / "new_sentiment_model.h5"
print(f"將模型儲存至: {new_model_path}")

# 解析一個來自設定檔的相對路徑
config_path_str = "../data/legacy_data.json"
absolute_path = resolve_path(config_path_str)
print(f"'{config_path_str}' 的絕對路徑是: {absolute_path}")
```

```