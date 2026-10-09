# components/ — 元件區（含芯片側元件）

可重複使用的零件事實卡。`done/` = 來源齊、驗證過、可被打包複製； `wip/`
= 草稿/候選/被擋住——**禁止宣稱完成、禁止被打包進完成組件**。芯片側元件在
`wip/chip/`；完成的芯片版圖正本在 repo 外
`/home/cxuo/chip/design/`（49 格 0/0），不複製進 repo（見 hardware/README.md 邊界）。規則與打包約束見 ../README.md；鎖測試 tests/unit/test_hardware_workspace.py。
