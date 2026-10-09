# components/ — 元件區（含芯片側元件）

可重複使用的零件事實卡。`done/` = 來源齊、驗證過、可被打包複製； `wip/`
= 草稿/候選/被擋住——**禁止宣稱完成、禁止被打包進完成組件**。芯片側元件在
`wip/chip/`；完成的芯片版圖正本在 repo 外
`/home/cxuo/chip/design/`（49 格 0/0），不複製進 repo（見 hardware/README.md 邊界）。規則與打包約束見 ../README.md；鎖測試 tests/unit/test_hardware_workspace.py。

> **區性**：本工作區是**設計與設計驗證區**——元件卡是選型事實文件，不是已採購的零件（未下單、未到貨、未量測）；見 hardware/README.md 區性聲明。
