"""Script to find corrupted METADATA files in site-packages"""
from pathlib import Path
import sys

# Check both site-packages locations
paths = [
    Path(r'C:\Users\Harsha Kumar\AppData\Roaming\Python\Python313\site-packages'),
    Path(sys.executable).parent.parent / 'Lib' / 'site-packages'
]

for sp in paths:
    if not sp.exists():
        continue
    print(f"\nChecking: {sp}")
    for p in sp.glob('*.dist-info'):
        meta = p / 'METADATA'
        if meta.exists():
            try:
                meta.read_text(encoding='utf-8')
            except Exception as e:
                print(f'  ERROR in {p.name}: {e}')
    print(f"  Done checking {sp.name}")
