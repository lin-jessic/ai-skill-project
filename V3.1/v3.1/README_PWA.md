# OpenShop LIFE Studio — PWA 遊戲版 v3.1

**舊版 Streamlit 介面保留，新版 V3.1 使用 `app_pwa.py` + `web/`。**

一個主 Skill / 三位 Agent / 六個互動模組 / 二十種店型。

## 快速啟動

Windows 在 `v3/` 先雙擊 `CHECK_ALL.cmd`，再雙擊 `START_PWA.cmd`，然後開啟 **http://127.0.0.1:8502/**。

```cmd
python -m pip install -r requirements_pwa.txt
python -m uvicorn app_pwa:app --host 127.0.0.1 --port 8502
```

## 六大功能

1. **開店法規**：符合店型的法規通關、官方查核入口（需人工確認）。
2. **員工、食材、設備**：營業 SOP 任務清單。
3. **老闆經營**：成本、損益兩平、敏感度與逐日決策模擬。
4. **商圈選址**：上傳 CSV/JSON，調整權重比較候選地點排行。
5. **外送通路**：平台費率、外送比例與包材成本情境。
6. **內用／外帶**：可調經營比例，非顧客偏好實測。

## 教授 DEMO

先選店型 → 上傳資料 → 市場分析 Agent 1 → 法規 Agent 2 → 開店程序兼審查 Agent 3 → 商圈 PK → 每日經營 → 匯出報告。

原始範例：`examples/DEMO_商圈資料_情境假設_非官方.csv`，**非官方，僅測試格式**。

## 手機與離線

`web/manifest.webmanifest`、`web/sw.js` 與 192/512 圖示已提供。
**手機必須使用 HTTPS 的已部署網站，才能完整測試安裝 PWA。** 在 PC 使用 localhost 僅適合本機開發；PWA 不會在離線時執行 Python 分析。

詳細操作、部署、驗證見 [docs/PWA_操作與部署.md](docs/PWA_操作與部署.md)，修正紀錄見 [docs/PWA_修正項目.md](docs/PWA_修正項目.md)。
