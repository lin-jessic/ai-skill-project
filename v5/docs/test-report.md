# A/B/C 啟動測試紀錄（平台自動觸發仍待獨立新對話驗證）

|測試|提示詞|預期|實際結果|啟動證據位置|修正紀錄|
|---|---|---|---|---|---|
|A|見 CODEX_DEMO_PROMPT.txt A|自動啟動|未確認；既有執行只能證明 Python 分階段流程|待補平台事件／新對話紀錄|本次開發除錯不列入正式證據|
|B|見 CODEX_DEMO_PROMPT.txt B|改寫仍啟動|尚未測試|待填|待填|
|C|見 CODEX_DEMO_PROMPT.txt C|不啟動|尚未測試|待填|待填|

Python 計算驗證見 python_test_log.txt；本次修正後為 15 項測試，另以 A1/A2 新 run 驗證人事成本與跨角色審查。這些都不是 Codex 啟動證據。正式提交前附實際提示詞全文與平台事件證據，轉成 PDF。

## V5 局部修正回歸（2026-11-27）

|項目|結果|證據|
|---|---|---|
|既有 unittest|15/15 通過|`docs/python_test_log.txt`|
|CHECK_V5.cmd|成功；官方資料檢查保留既有 WinError 10013|`CHECK_V5.cmd` 輸出、`data/official_download_manifest.json`|
|run.py all 整合入口|Stage 1–5 完成，notes 狀態如實標記缺少|`outputs/final_integration_v5_20261127/`|
|A1：2 人／85,000 元|保留使用者 payroll，Stage 5 提醒人事口徑需確認|`outputs/final_a1_v5_20261127/`|
|A2：3 人／未提供 payroll|混合教學估算 87,400 元，產生敏感度與人事警告|`outputs/final_a2_v5_20261127/`|
|A2：3 人／明確 85,000 元|保留 85,000 元，Stage 5 標記跨角色人事條件需確認|`outputs/regression_a2_v5_fixed_20261127/`|

Python 工具不會自動產生 `agent_notes_01.md` 至 `agent_notes_05.md` 或 `07_ai_business_advice.md`；正式 AI 流程須由 AI 在各階段實際寫入，不能用固定模板冒充。
