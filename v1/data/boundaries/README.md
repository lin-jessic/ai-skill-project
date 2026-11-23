# 行政區真實界線（選用）

若需要在地圖上繪製縣市／鄉鎮行政區界線，將 **官方或已核准使用、含正確座標的 GeoJSON** 存成 `townships.geojson` 放在本目錄。程式只會描繪真實匯入的幾何，不會用事故座標虛構行政區輪廓。

建議查詢：內政部國土測繪中心行政區域界線資料（https://www.nlsc.gov.tw/）或政府資料開放平臺（https://data.gov.tw/）。

- 需使用 WGS84（EPSG:4326），GeoJSON 座標順序是 `[經度, 緯度]`。
- 原始資料與授權資訊應記錄在 `references/data_sources.md`。
- 若沒有這份檔案，系統仍會顯示 OpenStreetMap 道路與地圖底圖，但不宣稱有官方行政區邊界。
