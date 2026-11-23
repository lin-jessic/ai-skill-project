# SafeRoad｜2024～2025 官方事故資料下載器

**放置位置：**把本 ZIP 裡的 `下載2024_2025官方事故資料.cmd` 和 `scripts/download_official_2024_2025.py` 放進現有專案 `1118_ch/`（腳本放進原本的 `scripts/`；其他檔案不必覆蓋）。**不要直接在獨立的下載包目錄執行**，否則資料會放到那份下載包內自己的 `data/raw/`。

你電腦的專案根目錄預計為：`C:\Users\user\Desktop\1118_ch_SafeRoad_v2_\1118_ch`，請以實際位置為準。

然後雙擊 `下載2024_2025官方事故資料.cmd`。下載器只使用警政署公開的 **113 年（2024）A1+A2**、**114 年（2025）A1+A2** 原始 ZIP；不產生任何模擬資料。下載時串流存檔，驗證 ZIP CRC、至少包含 CSV/JSON，最後記錄來源、時間、SHA-256。已存在且有效的同名 ZIP 不覆蓋。

資料會放到：

```text
1118_ch/
├─ 下載2024_2025官方事故資料.cmd
├─ scripts/
│  └─ download_official_2024_2025.py
└─ data/raw/
   ├─ 2024_A1_A2_official.zip
   ├─ 2024_A1_A2_official.zip.source.json
   ├─ 2025_A1_A2_official.zip
   ├─ 2025_A1_A2_official.zip.source.json
   └─ 2026_A1.json、2026_A2_*.zip（你之前已下載的資料，保留）
```

**官方連結：**
- 2024 (民國 113 年)：https://data.gov.tw/dataset/172969
- 2025 (民國 114 年)：https://data.gov.tw/dataset/177136

若 Python 下載失敗，從上面資料集網頁點 ZIP 下載，將 ZIP 直接存到 `data/raw/`，名稱對應 `2024_A1_A2_official.zip` / `2025_A1_A2_official.zip`。不要解壓，也不要把官網頁面 HTML 另存成 ZIP。

## 資料下載後，重新分析

在 VS Code CMD 的 `1118_ch` 根目錄：

```cmd
python scripts\run_all.py
python -m pytest -q
python -m streamlit run app.py
```

如有 Streamlit 已啟動，先按 Ctrl+C 結束原本程序，重新啟動。執行後年份篩選應根據**真正成功匯入的資料年份**顯示；如果某年度格式不符合現有解析器，請提供錯誤紀錄修正，不可假稱資料已被正確分析。

**重複計數提醒：** 2024 / 2025 全年 A1+A2 ZIP 各放一份，不要再把同年度的月份彙整檔複製進 `data/raw`。2026 為另一期資料，能繼續保留。不同事故類別資料也可能有多個當事者列，程式顯示的「來源筆數」不必然等於不同事故件數。

**下載器驗證限制：** 下載器驗證 ZIP 格式及 CRC，不保證每列的官方欄位與目前分析器完全一致；仍需跑 `run_all.py` 後檢查輸出與 `03_audit.json`。
