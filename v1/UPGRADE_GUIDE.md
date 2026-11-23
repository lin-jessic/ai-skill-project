# SafeRoad v2｜介面升級與多年度官方資料

## 這次修正

- 地圖底圖統一使用 **OpenStreetMap**，不再使用造成 `API KEY REQUIRED` 字樣的 CARTO 瓦片。
- 地圖可以切換 **群聚標記／密度格網／單筆事故點**。群聚模式解決紅點互相覆蓋；格網模式用明確的方格界線顯示集中區域。
- 支援選擇縣市、年份、月份、天候、事故類別及道路名稱。
- 新增時間圖、月份圖、天候圖、肇因排行、事故類型圖、縣市比較、雙區域比較與來源 CSV 下載。
- 欄位說明與計數口徑保留，Agent 3 驗證不通過時會禁止展示。
- 保留原始三角色 Skill 及舊程式檔，不刪除原始功能。

## 為什麼年份只有 2026？

因為 **目前匯入的來源檔案** 只含 2026 年。選單顯示來源資料中實際存在的年份，並不會憑空補舊年。
要有 2024、2025、2026，請先從官方平台分別取得真實歷史 JSON／CSV／ZIP，存放在 `data/raw/`，再合併執行：

```powershell
python scripts/run_pipeline.py --input data/raw/2024.zip data/raw/2025.zip data/raw/2026.json
python -m streamlit run app.py
```

實際檔名以你從政府網站下載的為準，請勿把不含事故資料的檔案混入。

- A1 原始資料：https://data.gov.tw/dataset/57023
- A1/A2 年度資料：https://data.gov.tw/dataset/177136

## 如何確認年份

在 VS Code Terminal 執行：

```powershell
python -c "import pandas as pd; x=pd.read_csv('outputs/01_normalized.csv'); print(x['year'].value_counts(dropna=False).sort_index())"
```

若要改成顯示其他年份，必須先下載那些年份的真實原始資料。

## 行政區界線

**地圖格網不等於行政區界線。** 如果要顯示正確的行政區界線，先取得官方 GeoJSON 並放在 `data/boundaries/townships.geojson`。詳見 `data/boundaries/README.md`。未下載官方行政區幾何前，不會虛構界線。

## 地圖仍沒有底圖時

OpenStreetMap 雖不需金鑰，仍需網路下載圖磚。檢查瀏覽器與學校網路是否阻擋 `tile.openstreetmap.org`。事故的本地統計圖和表格不依賴地圖瓦片。

## GitHub 版本更新

```powershell
git status
git add app.py scripts/run_pipeline.py data/boundaries/README.md UPGRADE_GUIDE.md README.md QUICK_START_中文.md tests/test_multiple_inputs.py
git commit -m "Improve dashboard UX and multi-year accident analysis"
git push origin main
```

請先測試，再執行 push。**不要把 CSV/JSON 大型原始資料、個資、Token、API Key 提交到公開 Repo。**

## 注意

這是歷史事故資料的學術探索工具，不能用來預測當前是否安全、不能從個案知道實際送醫醫院。若原始檔包含一事故多當事者列，必須用「資料列數」而不是「唯一事故件數」。
