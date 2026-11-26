OpenShop LIFE v4｜整合版快速開始

1. 在 Windows 進入本資料夾，第一次執行 CHECK_ALL.cmd。
2. 安裝依賴後，執行 START_PWA.cmd，開啟 http://127.0.0.1:8502/。
3. PWA 介面可建立店鋪、上傳 CSV/JSON、執行三角色分析、查看逐日模擬並下載報告。
4. 若要取得官方原始資料，執行「下載官方資料.cmd」，或使用：
   python -m scripts.download_official --only tax
   python -m scripts.download_official --all-months
   python -m scripts.download_official --check
5. 官方下載結果與 SHA-256 會寫入 data/official_download_manifest.json。

請先讀 readme.md 與 docs/，並保留 examples/ 檔案上的「非官方合成資料」標示。
