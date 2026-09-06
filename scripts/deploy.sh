#!/usr/bin/env bash
# Выкладка сайта на хостинг по SSH.
#
#   bash scripts/deploy.sh            обычная выкладка
#   bash scripts/deploy.sh --dry-run  показать, что будет сделано, ничего не менять
#
# Настройка один раз:
#   cp scripts/deploy.env.example deploy.env   и заполнить
#
# Порядок жёсткий и рассчитан на откат: сначала резервная копия действующего
# сайта, только потом изменения. Если что-то пойдёт не так, копия лежит на
# сервере и восстанавливается одной командой — она печатается в конце.
#
# Скрипт НИЧЕГО не удаляет на сервере. Файлы прежнего сайта, оставшиеся после
# распаковки, он только перечисляет: удалять их — решение человека, который
# видит сервер.
set -euo pipefail

cd "$(dirname "$0")/.."

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

if [ ! -f deploy.env ]; then
  echo "Нет файла deploy.env. Скопируйте scripts/deploy.env.example в deploy.env и заполните." >&2
  exit 1
fi
# shellcheck disable=SC1091
source deploy.env

: "${DEPLOY_SSH_HOST:?deploy.env: не задан DEPLOY_SSH_HOST}"
: "${DEPLOY_REMOTE_PATH:?deploy.env: не задан DEPLOY_REMOTE_PATH}"
DEPLOY_VENV="${DEPLOY_VENV:-$DEPLOY_REMOTE_PATH/.venv}"
DEPLOY_BACKUP_DIR="${DEPLOY_BACKUP_DIR:-\$HOME/texbiz-backups}"
SITE_URL="${DEPLOY_SITE_URL:-https://tex-biz.ru}"

if [ -n "$(git status --porcelain)" ]; then
  echo "В рабочем дереве есть незакоммиченные изменения — выкладывается только HEAD." >&2
  git status --short >&2
  exit 1
fi

COMMIT="$(git rev-parse --short HEAD)"
STAMP="$(date +%Y%m%d-%H%M%S)"
ARCHIVE="/tmp/texbiz-$COMMIT.tar.gz"

run_remote() {
  if [ "$DRY_RUN" = "1" ]; then
    echo "  [dry-run] ssh $DEPLOY_SSH_HOST '$1'"
  else
    ssh "$DEPLOY_SSH_HOST" "$1"
  fi
}

echo "Выкладка $COMMIT на $DEPLOY_SSH_HOST:$DEPLOY_REMOTE_PATH"
[ "$DRY_RUN" = "1" ] && echo "(холостой прогон, ничего не меняется)"
echo

# --- 1. Резервная копия ------------------------------------------------------
echo "1. Резервная копия действующего сайта"
BACKUP="$DEPLOY_BACKUP_DIR/texbiz-$STAMP.tar.gz"
run_remote "mkdir -p $DEPLOY_BACKUP_DIR && tar czf $BACKUP -C \"\$(dirname $DEPLOY_REMOTE_PATH)\" \"\$(basename $DEPLOY_REMOTE_PATH)\" && ls -lh $BACKUP"
echo

# --- 2. Сборка и доставка ----------------------------------------------------
echo "2. Сборка архива из HEAD"
git archive --format=tar.gz --output="$ARCHIVE" HEAD
echo "   $ARCHIVE ($(du -h "$ARCHIVE" | cut -f1))"

echo "3. Доставка на сервер"
if [ "$DRY_RUN" = "1" ]; then
  echo "  [dry-run] scp $ARCHIVE $DEPLOY_SSH_HOST:/tmp/"
else
  scp -q "$ARCHIVE" "$DEPLOY_SSH_HOST:/tmp/"
fi
echo

# --- 4. Распаковка -----------------------------------------------------------
# Распаковка поверх: .env и каталог данных архив не содержит, поэтому они
# остаются нетронутыми.
echo "4. Распаковка поверх текущей версии"
run_remote "mkdir -p $DEPLOY_REMOTE_PATH && tar xzf /tmp/$(basename "$ARCHIVE") -C $DEPLOY_REMOTE_PATH && rm /tmp/$(basename "$ARCHIVE")"
echo

# --- 5. Проверка .env --------------------------------------------------------
echo "5. Проверка настроек на сервере"
run_remote "test -f $DEPLOY_REMOTE_PATH/.env && echo '   .env на месте' || { echo '   ОШИБКА: нет .env — заполните его по образцу .env.example и повторите'; exit 1; }"
echo

# --- 6. Зависимости и данные -------------------------------------------------
echo "6. Зависимости, миграции, содержимое, статика"
run_remote "cd $DEPLOY_REMOTE_PATH && $DEPLOY_VENV/bin/pip install -q -r requirements.txt && $DEPLOY_VENV/bin/python manage.py migrate --noinput && $DEPLOY_VENV/bin/python manage.py loaddata services solutions articles && $DEPLOY_VENV/bin/python manage.py collectstatic --noinput | tail -2"
echo

# --- 7. Перезапуск -----------------------------------------------------------
# Passenger перечитывает приложение, когда меняется tmp/restart.txt.
echo "7. Перезапуск приложения"
run_remote "mkdir -p $DEPLOY_REMOTE_PATH/tmp && touch $DEPLOY_REMOTE_PATH/tmp/restart.txt && echo '   перезапуск запрошен'"
echo

# --- 8. Остатки прежнего сайта ----------------------------------------------
echo "8. Файлы прежнего сайта, оставшиеся в каталоге (ничего не удаляю)"
run_remote "cd $DEPLOY_REMOTE_PATH && ls -d app.py src build_release.sh deploy.sh VERSION 2>/dev/null || echo '   остатков не найдено'"
echo

# --- 9. Приёмка --------------------------------------------------------------
echo "9. Приёмка"
if [ "$DRY_RUN" = "1" ]; then
  echo "  [dry-run] python scripts/check_live.py $SITE_URL"
else
  sleep 5
  python scripts/check_live.py "$SITE_URL" || {
    echo
    echo "Приёмка не прошла. Откат:"
    echo "  ssh $DEPLOY_SSH_HOST 'rm -rf $DEPLOY_REMOTE_PATH && tar xzf $BACKUP -C \"\$(dirname $DEPLOY_REMOTE_PATH)\"'"
    exit 1
  }
fi

echo
echo "Готово. Резервная копия: $BACKUP"
echo "Откат, если понадобится:"
echo "  ssh $DEPLOY_SSH_HOST 'rm -rf $DEPLOY_REMOTE_PATH && tar xzf $BACKUP -C \"\$(dirname $DEPLOY_REMOTE_PATH)\"'"
