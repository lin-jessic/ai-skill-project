# VS Code 快速執行（Windows）

## 方法一：下載 ZIP 後一鍵操作
1. 解壓縮後，用 VS Code 開啟 `1118_ch` 資料夾。
2. 在檔案總管雙擊 `run_windows.bat`，或從 VS Code Terminal 輸入 `run_windows.bat`。
3. 它會安裝套件 → 下載政府 A1 真實資料 → 執行三角色程序 → 開啟 Streamlit。
4. 官方資料網站若擋住程式下載，請進入 https://data.gov.tw/dataset/57023 點 JSON 下載，把原始 JSON 放在 `data/raw/a1_official.json`，之後手動操作方法二。

## 方法二：完全手動
```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python scripts\download_data.py
python scripts\run_pipeline.py --input data\raw\a1_official.json
streamlit run app.py
```
如果使用官方年度 A1+A2 ZIP，請先人工下載到 data/raw，例如 `2025_official.zip`，接著將最後的分析命令輸入改成 `--input data/raw/2025_official.zip`。確認 ZIP 裡是真正的 CSV/JSON，而不是網站下載錯誤 HTML。

## 驗證
```powershell
python -m pytest -q
```
真正資料在本機跑成功後，請查看 `outputs/01_quality.json`、`outputs/02_summary.json`、`outputs/03_audit.json`、`outputs/03_report.md`。

## GitHub 推上去
```powershell
git init
git branch -M main
git add .
git commit -m "Build reproducible three-agent road safety skill"
git remote add origin https://github.com/YOUR_USERNAME/three-agent-skill.git
git push -u origin main
```
把 `YOUR_USERNAME` 換成你的 GitHub 帳號，先在 GitHub 建立空的 repository `three-agent-skill`。如你已先 clone repository，不要再 `git init`，直接 `git add .`、commit、push。**注意教授匿名規則**：交付或錄影前隱藏帳號名稱與組員資訊；若 repository 本身公開且有可辨識的 owner，請與組員確認匿名繳交方式。 Git history 不會因為刪除 README 姓名而匿名。

## Codex Skill
專案內 `.agents/skills/saferoad/SKILL.md` 提供專案級 Skill metadata，角色細節仍在根目錄 `agents/`。實際啟動證據必須由你使用的工具記錄，不能只憑 `run_pipeline.py` 執行成功。

## v2 更新：如果想看到其他年份、地圖界線與更多功能

請先閱讀 `UPGRADE_GUIDE.md`。這次新版使用免金鑰 OpenStreetMap，提供群聚、密度格網及單筆點模式；年份只會顯示你實際下載的官方資料年份。要合併多年度：

```powershell
python scripts/run_pipeline.py --input data/raw/2024.zip data/raw/2025.zip data/raw/2026.json
python -m streamlit run app.py
```

請把檔案名稱換成你實際下載的真實政府資料；不要把測試資料當成官方事故紀錄。

## CMD 一次跑全部原始事故資料（新增）

請勿在 CMD 貼 PowerShell 的 `$files`、`-eq`、`-ne` 語法。將官方 CSV、JSON、ZIP 放在 `data/raw/` 後，在專案根目錄雙擊 `run_all_cmd.bat` 即可。程式會安裝依賴、逐一搜尋原始資料、執行三角色分析、跑 pytest，再開啟 Streamlit。

也可逐步操作：

```cmd
python -m pip install -r requirements.txt
python scripts\run_all.py
python -m pytest -q
python -m streamlit run app.py
```

如果資料夾沒有原始資料，分析會明確中止，不會捏造任何事故數字。不要同時放入涵蓋相同事故期間的多份彙整檔，以免重複計數。
