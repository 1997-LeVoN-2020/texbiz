#!/usr/bin/env bash
# Возврат сайта к состоянию из резервной копии.
#
#   bash scripts/rollback.sh                        последняя копия
#   bash scripts/rollback.sh '$HOME/texbiz-backups/texbiz-….tar.gz'
#
# Копия распаковывается ПОВЕРХ, каталог сайта не удаляется. Так безопаснее и
# так этот откат уже отработал вживую. Побочный след: файлы, которых в копии
# нет, остаются лежать. Для прежнего Flask-сайта это безвредно, мешает только
# .htaccess нового сайта — он убирается переносом, а не удалением.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f deploy.env ]; then
  echo "Нет файла deploy.env." >&2
  exit 1
fi
# shellcheck disable=SC1091
source deploy.env
: "${DEPLOY_SSH_HOST:?deploy.env: не задан DEPLOY_SSH_HOST}"
: "${DEPLOY_REMOTE_PATH:?deploy.env: не задан DEPLOY_REMOTE_PATH}"
DEPLOY_BACKUP_DIR="${DEPLOY_BACKUP_DIR:-\$HOME/texbiz-backups}"

BACKUP="${1:-}"

ssh "$DEPLOY_SSH_HOST" "set -e
BK='$BACKUP'
[ -n \"\$BK\" ] || BK=\$(ls -t $DEPLOY_BACKUP_DIR/*.tar.gz | head -1)
echo \"восстанавливаю из: \$BK\"
tar xzf \"\$BK\" -C \"\$(dirname $DEPLOY_REMOTE_PATH)\"
mkdir -p /tmp/texbiz-disabled
mv $DEPLOY_REMOTE_PATH/.htaccess /tmp/texbiz-disabled/ 2>/dev/null && echo '.htaccess нового сайта убран' || true
mkdir -p $DEPLOY_REMOTE_PATH/tmp && touch $DEPLOY_REMOTE_PATH/tmp/restart.txt
echo 'перезапуск запрошен'"

echo
echo "Жду перезапуска и проверяю."
sleep 12
python scripts/check_live.py "${DEPLOY_SITE_URL:-https://tex-biz.ru}" || true
