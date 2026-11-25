OpenShop AI v2 - Full automatic official data downloader (Windows CMD)

1. Unzip this archive.
2. Copy download_official.cmd into YOUR v2 root folder.
3. Copy scripts/download_official.py into YOUR v2/scripts folder (overwrite).
4. Double-click download_official.cmd. No browser/file picker is used.
5. Data will be saved under v2/data/raw/{tax,population,transit,market}.
6. Log/errors/URLs/SHA256 saved to v2/data/official_download_manifest.json.

Official dataset IDs: 9400, 77132, 164957, 25346, 94937.
Default CMD downloads ALL published monthly resources for 2024-2026 where available,
plus one tax ZIP and one restaurant statistics CSV. This can take a while.
If a source server blocks access, the program logs an error. It never invents data.

CMD alternative for fewer files (latest published month in each year):
  python -m scripts.download_official
For all months:
  python -m scripts.download_official --all-months
To check local files:
  python -m scripts.download_official --check

NOTE: The downloader collects files. It does not magically transform five unrelated
raw government schemas into the professor's demo CSV format. That requires a
separate data integration/ETL task.
