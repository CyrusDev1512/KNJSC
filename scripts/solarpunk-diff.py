"""Tách đúng thay đổi UI khỏi trạng thái chưa commit được mang theo lúc bắt đầu."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

root = Path(__file__).resolve().parents[1]
baseline = root.parent / 'ui-solarpunk-baseline-20260914'
manifest = json.loads((baseline / 'manifest.json').read_text(encoding='utf-8'))
out = root / 'artifacts/solarpunk'
compare = out / 'compare'
paths = subprocess.check_output(['git', 'ls-files', '-co', '--exclude-standard', '-z'], cwd=root).decode().split('\0')
changed = []
for name in sorted(set(filter(None, paths))):
    target = root / name
    current = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
    old = manifest.get(name)
    if current == old:
        continue
    changed.append({'path': name, 'baseline': old, 'current': current})
    for side, source in [('a', baseline / 'tree' / name), ('b', target)]:
        destination = compare / side / name
        if source.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
with (out / 'ui-only.patch').open('wb') as stream:
    subprocess.run(['git', '-c', 'core.autocrlf=false', 'diff', '--no-index', '--no-prefix', '--binary', 'a', 'b'], cwd=compare, stdout=stream, check=False)
(out / 'ui-files.json').write_text(json.dumps(changed, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'{len(changed)} tệp UI; patch: {out / "ui-only.patch"}')
