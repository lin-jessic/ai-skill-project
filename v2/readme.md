# OpenShop AI v2｜你的第一間店，開得起來嗎？

台灣開店三角色 AI Skill、官方公開資料商圈探索、營運管理和財務情境 Dashboard。

**版本狀態：可執行的研究原型（不是已取得開店許可、不是精準客流預測）。**

## 六個模組

1. 法規登記與合法開店事項：官方查核入口 + 待確認清單。
2. 店員作業與食材設備管理：依店型切換 SOP。
3. 老闆財務試算：可調整售價、月租、人工、訂單與成本。
4. 商圈選址：如實顯示人口、縣市登記家數、桃園捷運運量；資料不存在時不產生分數。
5. 外送通路：提供官方／平台公開服務範圍查核入口和抽成成本試算。
6. 內用、外帶、外送：調整情境占比，**不宣稱這是實際消費偏好**。

## Windows 快速啟動

在 Windows 10/11、VS Code 安裝 Python 3.11+，於 `v2` 根目錄：

```cmd
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

或雙擊 `啟動OpenShop.cmd`。第一次開啟如果尚未下載資料，商圈頁會如實顯示「未取得」，但法遵、SOP、財務情境與報告仍可使用。

下載官方資料：雙擊 `下載官方資料.cmd`，或執行：

```cmd
python -m scripts.download_official
```

下載後資料自動放到 `data/raw` 子資料夾。**實際下載需要連線政府主機，本 ZIP 的 `data/raw` 不預先包含原始檔。** 可到 `references/data_sources.md` 的官方資料頁手動下載。部分政府主機可能擋程式下載，請看終端機輸出。

### 執行三角色 Pipeline + 單元測試

```cmd
python -m pytest -q
python -m scripts.run_pipeline --config config_example.json
```

輸出在 `outputs/`：

- `01_legal.json`：法規確認清單
- `01_operations.json`：每日 SOP
- `02_market.json`：官方資料有無與解析結果
- `03_finance.json`：可驗算財務試算
- `03_business_report.md`：專屬開店報告
- `04_audit.json`：數學一致性審查與未確認事項

CLI 執行 Python 角色流程，**不等於已證明 ChatGPT／Codex 自動觸發 Skill**。自動觸發測試需在真正支援 Skill 的環境另行錄影與截圖。

## 不同於一般 AI 生成報告的地方

- 每個官方來源可追溯網址、下載時間、SHA-256（`data/download_manifest.json`）。
- 只有成功取得且能解析的資料才進行統計；禁止填造官方紀錄。
- 假設成本與官方資料嚴格分離；財務式可用 pytest 驗證。
- 不將某行政區人口當作店鋪來客數，也不以捷運運量推導外送需求。
- 擴充時可加入企業調查、商家地理編碼、問卷（需注明樣本數）和不同候選店址比較。

## 資料與法律限制

請看 `references/data_sources.md`。合法開店必須依實際地址與業態向主管機關確認。外送平台即時服務範圍、顧客內用偏好與租金市價不在本專案已接入的官方原始資料中。程式中的預設情境僅作試算，**不能作為投資報酬保證**。

## GitHub 目錄放置

將整個 `OpenShop_AI_v2` 資料夾內容放在 `three-agent-skill/v2/`，保留原本 `v1` 不變。`.gitignore` 預設排除大型下載原始檔與生成的輸出，其他人 Clone 後請依本 README 重新下載。
