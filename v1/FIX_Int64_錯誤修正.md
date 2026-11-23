# 2026 官方事故資料：Int64 缺值處理修正

## 問題
八份真實官方檔案已下載，Agent 1 成功讀取，但 Agent 2 在 `scripts/core.py` 的 `summary()` 計數時，對 `year` 的 pandas 可空整數欄位（`Int64`）直接使用 `fillna("未提供")`，導致 `TypeError: Invalid value '未提供' for dtype 'Int64'`。

## 修正
先用 `.astype("string")` 將計數用的欄位轉成字串，再用 `.fillna("未提供")` 補缺值。年分欄位在原始標準化資料仍維持數值型態，不會被修改或補造年份。

## 在 Windows 上操作
1. 關閉原本的命令提示字元視窗（若 Streamlit 尚在執行，先 `Ctrl+C`）。
2. 從修補 ZIP 取出 `scripts/core.py` 與 `tests/test_core.py`，覆蓋你既有專案相同路徑的檔案（不碰 `data/raw`）。
3. 開啟 CMD，切換到專案資料夾，執行：

```cmd
python -m pytest -q
python scripts\run_all.py
python -m streamlit run app.py
```

或直接雙擊原本的 `run_all_cmd.bat`。

## 驗證範圍
- 六項單元測試通過。
- 人工測試資料僅存在於臨時資料夾中用於測試，不含在專案資料，亦不作為事故分析成果。
- 正式八份資料仍需在使用者 Windows 電腦端重跑，未宣稱已完成正式資料驗證。
