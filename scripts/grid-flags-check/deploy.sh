#!/usr/bin/env bash
# Chỉ chạy sau khi đã duyệt phát hành và kiểm chứng đúng commit.
# Các cờ thử nghiệm không vượt qua sàng lọc, không phát hành ở trạng thái bật.
set -euo pipefail
target="$1"
variant="${2:-off}"
[[ "$target" =~ ^[0-9a-f]{40}$ ]]
[[ "$variant" = off ]]
folder="/opt/knjsc-runtime/release-grid-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 "$folder"
cd /opt/knjsc
test -z "$(git status --porcelain)"
git fetch origin codex/crm-update-solar-ui
git merge-base --is-ancestor "$target" origin/codex/crm-update-solar-ui
git merge-base --is-ancestor HEAD "$target"
git rev-parse HEAD > "$folder/commit.before"
sha256sum app/static/css/crm-frame.css app/static/css/master-grid.css > "$folder/css.before"
cp /opt/knjsc-runtime/.env "$folder/env.before"
chmod 600 "$folder/env.before"
docker inspect --format '{{.Name}} {{.Config.Image}} {{.HostConfig.Memory}} {{.HostConfig.NanoCpus}}' \
  knjsc-production-crm-1 knjsc-production-erp-1 knjsc-production-worker-1 knjsc-production-heavy-1 knjsc-production-beat-1 > "$folder/images.before"
docker exec knjsc-production-db-1 sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$folder/database.dump"
test -s "$folder/database.dump"
docker exec -i knjsc-production-db-1 pg_restore --list < "$folder/database.dump" > "$folder/database.list"
sha256sum "$folder/database.dump" > "$folder/database.sha256"
git merge --ff-only "$target"
sha256sum -c "$folder/css.before"
image="knjsc-app:${target:0:7}-grid"
docker build -f deploy/Dockerfile -t "$image" .
cd /opt/knjsc-runtime
compose=(docker compose -f compose.yml -f compose.vps.yml)
KNJSC_IMAGE="$image" "${compose[@]}" run --rm --no-deps crm python manage.py check
KNJSC_IMAGE="$image" "${compose[@]}" run --rm --no-deps erp python manage.py check
rollback() {
  trap - ERR
  cp "$folder/env.before" .env
  "${compose[@]}" run --rm --no-deps crm python manage.py collectstatic --noinput
  "${compose[@]}" --profile heavy up -d --no-deps erp crm worker heavy beat
  docker exec knjsc-production-proxy-1 nginx -t
  docker exec knjsc-production-proxy-1 nginx -s reload
  echo 'Rolled back runtime image/config; database unchanged.'
  exit 1
}
trap rollback ERR
python3 - "$image" "$variant" <<'PY'
import re, sys
from pathlib import Path
p=Path('.env'); content=p.read_text()
values={'KNJSC_IMAGE':sys.argv[1]}
variant=sys.argv[2]
for flag in ['READ','SYNC','RENDER','RECEIPTS','STATS','EXPORT','QUEUES']:
    enabled=(flag=='READ' and variant in ('read','sync')) or (flag=='SYNC' and variant=='sync') or (flag=='RENDER' and variant=='render')
    values['CRM_OPT_'+flag]=str(int(enabled))
for key,value in values.items():
    pattern=r'^'+key+r'=.*$'
    if re.search(pattern,content,re.M):content=re.sub(pattern,key+'='+value,content,flags=re.M)
    else:content+='\n'+key+'='+value+'\n'
p.write_text(content)
PY
"${compose[@]}" config --quiet
"${compose[@]}" run --rm --no-deps crm python manage.py collectstatic --noinput
"${compose[@]}" --profile heavy up -d --no-deps erp crm worker heavy beat
docker exec knjsc-production-proxy-1 nginx -t
docker exec knjsc-production-proxy-1 nginx -s reload
for domain in erp.thnsolution.io.vn crm.thnsolution.io.vn; do
  passed=0
  for attempt in $(seq 1 20); do
    status=$(curl -s -o /dev/null -w '%{http_code}' "https://$domain/dang-nhap/")
    if [ "$status" = 200 ]; then passed=1; break; fi
    sleep 2
  done
  test "$passed" = 1
  echo "$domain HTTP $status"
done
docker inspect --format '{{.Name}} {{.Config.Image}} {{.HostConfig.Memory}} {{.HostConfig.NanoCpus}}' \
  knjsc-production-crm-1 knjsc-production-erp-1 knjsc-production-worker-1 knjsc-production-heavy-1 knjsc-production-beat-1 > "$folder/images.after"
cat "$folder/images.after"
python3 - "$folder/images.before" "$folder/images.after" "$image" <<'PY'
import sys
from pathlib import Path
before = {parts[0]: parts for parts in map(str.split, Path(sys.argv[1]).read_text().splitlines())}
after = {parts[0]: parts for parts in map(str.split, Path(sys.argv[2]).read_text().splitlines())}
assert before.keys() == after.keys(), 'Danh sách dịch vụ thay đổi'
for name, parts in after.items():
    assert parts[1] == sys.argv[3], f'{name}: sai image'
    assert parts[2:] == before[name][2:], f'{name}: giới hạn tài nguyên bị thay đổi'
PY
echo "Commit $target; variant $variant; backup $folder"
