#!/usr/bin/env bash
# Собирает архив для загрузки на хостинг из того, что закоммичено в HEAD.
#
#   bash scripts/build_release.sh
#
# Кладёт releases/texbiz-django-<дата>-<коммит>.zip. В архив попадает только
# закоммиченное (git archive) и без того, что помечено export-ignore
# в .gitattributes: .claude/, docs/, scripts/, README.md.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -n "$(git status --porcelain)" ]; then
  echo "В рабочем дереве есть незакоммиченные изменения:" >&2
  git status --short >&2
  echo >&2
  echo "Сначала закоммитьте их — в архив попадает только HEAD." >&2
  exit 1
fi

mkdir -p releases

STAMP="$(date +%Y%m%d)"
COMMIT="$(git rev-parse --short HEAD)"
OUT="releases/texbiz-django-${STAMP}-${COMMIT}.zip"

if [ -e "$OUT" ]; then
  echo "Файл $OUT уже существует, ничего не перезаписываю." >&2
  exit 1
fi

git archive --format=zip --output="$OUT" HEAD

echo "Собрано: $OUT"
unzip -l "$OUT" | tail -n 1
echo
echo "Дальше на сервере: распаковать, заполнить .env, затем"
echo "  .venv/bin/pip install -r requirements.txt"
echo "  .venv/bin/python manage.py migrate"
echo "  .venv/bin/python manage.py loaddata services solutions articles"
echo "  .venv/bin/python manage.py collectstatic --noinput"
echo "и перезапустить приложение в ISPmanager."
