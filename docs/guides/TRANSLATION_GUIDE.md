# Unified-AI-Project 翻譯指南

本文檔介紹了如何為 Unified-AI-Project 添加和更新翻譯。

## 概述

本專案使用 `Babel` 工具結合自定義腳本 `scripts/translation_helper.py` 來管理翻譯。翻譯字串存儲在標準的 `.po` 文件中，並編譯成 `.mo` 文件供應用程式使用。

支持的語言目前包括：
*   英文 (en) - 預設語言，原文
*   中文 (zh)
*   日文 (ja)

翻譯檔案位於 `locales/` 目錄下，結構如下：
```
locales/
├── en/
│   └── LC_MESSAGES/
│       ├── messages.po
│       └── messages.mo
├── ja/
│   └── LC_MESSAGES/
│       ├── messages.po
│       └── messages.mo
├── zh/
│   └── LC_MESSAGES/
│       ├── messages.po
│       └── messages.mo
└── messages.pot  # 翻譯模板檔案
```

## 翻譯流程

### 1. 標記待翻譯字串

#### Python 程式碼
在 Python 程式碼 (`.py` 文件，主要位於 `src/` 目錄下) 中，使用 `_()` 函數包裹需要翻譯的字串。

首先，確保在文件頂部導入了 `_` 函數。一個基本的設定（如 `src/interfaces/cli/main.py` 中所示）是：
```python
import gettext
import os

try:
    app_lang = os.environ.get('APP_LANG', 'en')
    locales_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'locales')
    translation = gettext.translation('messages', localedir=locales_path, languages=[app_lang], fallback=True)
    translation.install()
    _ = translation.gettext
except FileNotFoundError:
    _ = lambda s: s # Fallback
```

然後，像這樣使用 `_()`：
```python
print(_("This is a translatable string."))
greeting = _("Hello, {name}!").format(name="User")
```

#### Markdown 文件 (docs/)
Markdown 文件的翻譯字串提取功能 (`extract-md`) 目前在 `translation_helper.py` 中尚為佔位符。一旦實現，這裡將更新具體的標記或提取約定。通常，這可能涉及提取所有文本段落，或使用特殊的註解標記。

### 2. 提取字串並更新翻譯檔案

當你在程式碼中添加了新的待翻譯字串，或者修改了現有的字串後，需要執行以下步驟：

1.  **提取 Python 字串到模板 (`.pot` 文件)：**
    ```bash
    python scripts/translation_helper.py extract-py
    ```
    這會掃描 `src/` 目錄下的 Python 文件，並更新 `locales/messages.pot` 模板檔案。

2.  **(未來步驟) 提取 Markdown 字串：**
    當 `extract-md` 功能實現後，會有相應的命令。

3.  **更新各語言的 `.po` 檔案：**
    ```bash
    python scripts/translation_helper.py update
    ```
    此命令會使用 `locales/messages.pot` 中的最新字串來更新 `locales/en/LC_MESSAGES/messages.po`、`locales/ja/LC_MESSAGES/messages.po` 和 `locales/zh/LC_MESSAGES/messages.po`。
    新的字串會被添加進去，而原始碼中已被移除的字串可能會被標記為過時 (fuzzy) 或被註解掉。

### 3. 進行翻譯

編輯各語言對應的 `.po` 文件 (例如 `locales/zh/LC_MESSAGES/messages.po`)。
在每個 `msgid` (原文) 下方，將翻譯填寫到 `msgstr` (譯文) 中。

例如：
```po
#: src/interfaces/cli/main.py:147
msgid "Send a query to the AI"
msgstr "向 AI 發送查詢"
```
對於包含變數的字串 (例如使用了 `.format()` 或 f-string)，請確保翻譯後的字串也包含相應的佔位符：
```po
#: src/interfaces/cli/main.py:91
#, python-brace-format
msgid "CLI: Sending query to DialogueManager: '{query_text}'"
msgstr "CLI：正在向對話管理器發送查詢：'{query_text}'"
```

**注意：**
*   `.po` 文件是 UTF-8 編碼。
*   `PO-Revision-Date` 和 `Last-Translator` 等頭部欄位應在首次翻譯時更新。

### 4. 編譯翻譯檔案

完成翻譯後，需要將 `.po` 文件編譯成應用程式可以高效讀取的二進制 `.mo` 文件：
```bash
python scripts/translation_helper.py compile-langs
```
這會為 `locales` 目錄下所有語言的 `.po` 文件生成對應的 `.mo` 文件。

## 運行應用程式以查看翻譯

對於 `src/interfaces/cli/main.py` 中的 CLI 示例，可以通過設定 `APP_LANG` 環境變數來選擇語言：

```bash
# 查看中文翻譯 (假設已翻譯並編譯)
APP_LANG=zh python src/interfaces/cli/main.py query "some query"

# 查看日文翻譯
APP_LANG=ja python src/interfaces/cli/main.py query "some query"

# 預設或 APP_LANG=en 將顯示英文原文
python src/interfaces/cli/main.py query "some query"
```

## 翻譯輔助工具 (`scripts/translation_helper.py`) 命令摘要

*   `python scripts/translation_helper.py extract-py [--verbose]`: 從 Python 檔案提取字串到 `.pot` 模板。
*   `python scripts/translation_helper.py extract-md [--md_dir PATH] [--verbose]`: (佔位符) 從 Markdown 檔案提取字串。
*   `python scripts/translation_helper.py update [--verbose]`: 從 `.pot` 模板更新所有語言的 `.po` 檔案。
*   `python scripts/translation_helper.py compile-langs [--verbose]`: 編譯所有語言的 `.po` 檔案到 `.mo` 檔案。

使用 `--verbose` 選項可以查看更詳細的執行輸出。
使用 `--help` 查看所有命令和選項，例如 `python scripts/translation_helper.py --help`。

## 注意事項
* 在運行 `translation_helper.py` 腳本之前，請確保您已經在專案的虛擬環境中 (`source venv/bin/activate`)，並且已經安裝了必要的依賴 (`pip install Babel click`)。
```
