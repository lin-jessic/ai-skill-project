# OpenShop LIFE v3｜完整修復版使用方式

本 ZIP 是 **一整個 v2 資料夾**；包含原有 Streamlit 與三角色分析、遊戲式 PWA、後端 API、資料下載程式、測試和文件。

## 替換方式（重要）

1. 關閉先前 CMD 中的 Uvicorn（Ctrl+C）。
2. 把你電腦原本的 `ai-skill-project/v2` 改名為 `v2_backup`（避免遺失資料與自訂修改）。
3. 解壓縮本包，把裡面的 `v2` 資料夾複製到 `ai-skill-project/`，讓 `app_pwa.py` 位於 `ai-skill-project/v2/app_pwa.py`。
4. 如果舊 `v2_backup/data/raw/` 有已下載的政府資料，請**只複製該目錄內的原始資料**到新版對應目錄；不要整個舊 `web/` 覆蓋新版。
5. 第一次執行先雙擊 `CHECK_ALL.cmd`，確認所有測試通過；再雙擊 `START_PWA.cmd`。
6. Chrome 開 `http://127.0.0.1:8502/`。若仍有舊畫面，F12 → Application → Service Workers → Unregister，並清除這個本機站點快取後重載。

## 兩個入口

- 遊戲 PWA：`START_PWA.cmd` 或 `python -m uvicorn app_pwa:app --host 127.0.0.1 --port 8502`
- 原 Streamlit 舊版：`python -m streamlit run app.py`

## 本次已驗證

- `verify_web.py` 會確認 HTML/CSS/JS/SW/manifest 與 PNG 圖示位置正確。
- Python `pytest`：23 項通過（於此環境完成）。
- FastAPI TestClient：首頁、CSS、JS、SW、manifest、favicon、20 店型 API 全部 200 且 MIME／內容符合。
- 尚未在你的 Windows 電腦實際雙擊或以手機安裝 PWA，需你本機確認。

## 重要限制

- `examples/` 的 CSV 是教學用假設資料，**不是政府真實統計**。
- 真實政府資料需依 `references/` 與下載器取得；資料下載與商圈整合是不同步驟。
- 網站執行三階段 Python 程序不等於 AI 模型自動觸發 `SKILL.md`，教授的觸發 A/B/C 測試須在真正的 AI Skill 環境驗證。
- iPhone / Android 安裝 PWA 一般需要 HTTPS 部署；本機 127.0.0.1 只供桌面測試。
