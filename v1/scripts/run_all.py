"""在 Windows CMD / PowerShell 均可執行：找出所有真實資料並執行三角色流程。"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
SUPPORTED = {'.csv', '.json', '.zip'}


def main() -> int:
    files = sorted(
        p for p in RAW.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED
        and not p.name.lower().endswith('.source.json')
        and p.stat().st_size > 0
    ) if RAW.exists() else []
    if not files:
        print('找不到真實事故資料！請先將官方 CSV / JSON / ZIP 放進 data/raw。')
        print('資料來源：https://data.gov.tw/dataset/57023')
        return 2
    print(f'找到 {len(files)} 個原始資料檔：')
    for p in files:
        print(f'  {p.name} ({p.stat().st_size:,} bytes)')
    print('注意：請避免放入重疊期間的事故彙整檔，否則可能重複計數。')
    result = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'run_pipeline.py'), '--input', *(str(p) for p in files)],
        cwd=ROOT,
        check=False,
    )
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
