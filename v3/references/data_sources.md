# 政府公開資料來源與統計口徑

資料頁與直接端點於 2026-11-25 查核。**本 ZIP 不包含未成功下載的官方原始檔，檔案存在與否請以 `data/raw` 為準。**

| key | 官方來源 | 直接下載 | 期間 | 用途 | 限制 |
|---|---|---|---|---|---|
| tax | [財政部全國稅籍登記 9400](https://data.gov.tw/dataset/9400) | https://eip.fia.gov.tw/data/BGMOPEN1.zip | 官方更新中 | 商家登記地址與行業 | 登記非實際營業；檔案大；不能從粗地址直接產生 500 公尺競爭數 |
| population | [村里戶數與單齡人口 77132](https://data.gov.tw/dataset/77132) | https://opdadm.moi.gov.tw/api/v1/no-auth/resource/api/dataset/2C7688CB-B505-4D00-B11C-66C4D31B024F/resource/008BCB78-3608-48AB-8431-BB7377340424/download | 2025/12 | 行政區人口 | 欄位與格式需在下載後核對，不代表來客數 |
| metro | [桃園捷運運量 164957](https://data.gov.tw/dataset/164957) | https://opendata.tycg.gov.tw/api/dataset/7a7e006b-ec19-47ad-8fc8-6640a7a72f8a/resource/3ec59f62-b35c-4469-8b8a-145f22ec8318/download | 2026/06 | 站體平均日運量 | 車站運量不是店門口人流 |
| industry | [商業登記家數 25346](https://data.gov.tw/dataset/25346) | https://data.gcis.nat.gov.tw/od/file?oid=7C2E10AC-AC3B-4E84-B30B-FC62D32FB5F7 | 2026/02 | 縣市住宿餐飲大類家數 | 不等於所有營業中店家或飲料店數 |
| restaurant | [經濟部餐飲業統計 94937](https://data.gov.tw/dataset/94937) | https://www.moea.gov.tw/MNS/populace/content/wHandMenuFile.ashx?file_id=19466 | 不定期 | 產業背景 | 可能隨下載資源更新而變更檔案 |

另有法規參考入口：
- [經濟部公司與商業一站式申請](https://onestop.nat.gov.tw/)
- [食藥署食品良好衛生規範](https://www.fda.gov.tw/TC/siteContent.aspx?sid=3077)
- [勞動部法規查詢](https://laws.mol.gov.tw/)
- [財政部稅務入口網](https://www.etax.nat.gov.tw/)

## 下載失敗時

網站可能設定防爬機制、TLS／連線限制、暫時性的官方站臺錯誤。下載器將失敗顯示 `[FAIL]`，絕不填入自造資料。使用官網手動下載，**依 key 對照上表放至 `data/raw`**（必須使用程式要求的檔名），或者調整 `scripts/logic.py` 的 `SOURCES` 檔名與下載器設定。資料下載不等於已正確解析，請檢視 Dashboard 和執行測試。

## 研究限制

2026/02 商業統計與 2025/12 人口、2026/06 運量的時間點不同。不得計算「精確的同時期商圈分數」。若需 2024–2026 年度連續比較，應另建相同口徑時序資料集並控管缺月。外送訂單量與內外帶偏好不是這些官方資料直接包含的欄位。
