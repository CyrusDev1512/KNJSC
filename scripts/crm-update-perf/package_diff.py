"""Diff chiến dịch so với snapshot có dirty state, không so nhầm HEAD."""
import difflib
import hashlib
import json
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
evidence=root/'storage/crm-update'
manifest=json.loads((evidence/'manifest.json').read_text(encoding='utf-8'))
baseline=evidence/'baseline'
paths=set(subprocess.check_output(['git','ls-files','-c','-o','--exclude-standard','-z'],cwd=root).decode().split('\0'))-{''}
paths.update(manifest['sha256'])
patch=[];changes=[]
for name in sorted(paths):
    if name.startswith('storage/') or (name.startswith('app/.') and ('ready' in name or 'result' in name)):
        continue
    before=baseline/name;after=root/name
    old=before.read_bytes() if before.is_file() else None
    new=after.read_bytes() if after.is_file() else None
    old_hash=hashlib.sha256(old).hexdigest() if old is not None else None
    new_hash=hashlib.sha256(new).hexdigest() if new is not None else None
    if name in manifest['sha256']:
        assert old_hash==manifest['sha256'][name],f'Snapshot changed: {name}'
    if old_hash==new_hash:continue
    changes.append({'file':name,'status':'added' if old is None else 'deleted' if new is None else 'modified',
                    'baseline_dirty':name in manifest['dirty'],'before':old_hash,'after':new_hash})
    patch.append(f'diff --git a/{name} b/{name}\n')
    try:
        # Hash vẫn giữ byte gốc; diff để review bỏ nhiễu CRLF/LF trên Windows.
        old_text=(old or b'').decode('utf-8').replace('\r\n','\n').splitlines(keepends=True)
        new_text=(new or b'').decode('utf-8').replace('\r\n','\n').splitlines(keepends=True)
        patch.extend(difflib.unified_diff(old_text,new_text,
            fromfile=f'a/{name}' if old is not None else '/dev/null',
            tofile=f'b/{name}' if new is not None else '/dev/null'))
    except UnicodeDecodeError:
        patch.append(f'Binary files a/{name} and b/{name} differ\n')
(evidence/'campaign.diff').write_text(''.join(patch),encoding='utf-8')
(evidence/'campaign-files.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'changed':len(changes),'added':sum(c['status']=='added' for c in changes),
    'deleted':sum(c['status']=='deleted' for c in changes),'baseline_files_checked':len(manifest['sha256'])}))
