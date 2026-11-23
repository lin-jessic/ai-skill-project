# Data sources and provenance

1. Primary official A1 JSON: https://data.gov.tw/dataset/57023 (National Police Agency; A1 = fatal at scene or within 24 hours). Resource URL is embedded in `scripts/download_data.py`.
2. A1 and A2 2025 annual ZIP: https://data.gov.tw/dataset/177136 . Download on the official page and save to `data/raw/` if direct endpoint changes.
3. Dataset definitions: A1 fatal accidents within 24 hours; A2 injury accidents or death after 24 hours, according to official metadata.

The title *real-time* on 57023 does not promise live alerts. Its metadata says irregular updates.
Never silently combine sources across different years or count a multi-party record as a distinct accident event.
For all source files, save byte-level SHA256, input file name and execution timestamp in quality JSON.
This project does not contain inferred real accident rows. No `sample_accidents.csv` fabricated for the public dashboard.
