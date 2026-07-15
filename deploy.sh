#!/bin/bash
# Deploy the committed HEAD straight to tex-biz.ru over SFTP/SSH.
#
# Same "ship exactly what's committed, nothing extra" rule as
# build_release.sh: uses `git archive HEAD` (respects .gitattributes
# export-ignore), so dev-only files never reach the server. Uncommitted
# changes are NOT deployed -- commit first.
#
# Setup (one-time):
#   cp deploy.env.example deploy.env
#   # fill in DEPLOY_HOST / DEPLOY_USER / DEPLOY_SSH_KEY (or leave key
#   # empty to be prompted for a password) / DEPLOY_REMOTE_PATH
#
# Usage:
#   bash deploy.sh

set -e

cd "$(dirname "$0")"

if [ ! -f deploy.env ]; then
    echo "==> deploy.env not found."
    echo "    cp deploy.env.example deploy.env, then fill in your real connection details."
    exit 1
fi

# shellcheck disable=SC1091
source deploy.env

: "${DEPLOY_HOST:?deploy.env: DEPLOY_HOST is empty}"
: "${DEPLOY_USER:?deploy.env: DEPLOY_USER is empty}"
: "${DEPLOY_REMOTE_PATH:?deploy.env: DEPLOY_REMOTE_PATH is empty}"
DEPLOY_PORT="${DEPLOY_PORT:-22}"

if [ -n "$(git status --porcelain)" ]; then
    echo "==> Warning: working tree has uncommitted changes."
    echo "    deploy.sh ships 'git archive HEAD' -- uncommitted changes will NOT be deployed."
    echo ""
fi

SSH_OPTS=(-P "$DEPLOY_PORT")
if [ -n "$DEPLOY_SSH_KEY" ]; then
    SSH_OPTS+=(-i "$DEPLOY_SSH_KEY")
fi

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

echo "==> Exporting committed HEAD ($(git rev-parse --short HEAD))..."
git archive HEAD | (cd "$WORKDIR" && tar -x)

echo "==> Uploading to $DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_REMOTE_PATH ..."
sftp "${SSH_OPTS[@]}" "$DEPLOY_USER@$DEPLOY_HOST" <<EOF
-mkdir $DEPLOY_REMOTE_PATH
put -r $WORKDIR/* $DEPLOY_REMOTE_PATH
bye
EOF

echo ""
echo "Done. Files uploaded to $DEPLOY_REMOTE_PATH."
echo ""

if [ -n "$DEPLOY_SSH_KEY" ]; then
    echo "==> Restarting Passenger app (touch tmp/restart.txt)..."
    ssh -p "$DEPLOY_PORT" -i "$DEPLOY_SSH_KEY" "$DEPLOY_USER@$DEPLOY_HOST" \
        "mkdir -p '$DEPLOY_REMOTE_PATH/tmp' && touch '$DEPLOY_REMOTE_PATH/tmp/restart.txt'"
    echo "Done -- Passenger will reload the app on the next request."
else
    echo "==> No DEPLOY_SSH_KEY set, so the app wasn't restarted automatically."
    echo "    Restart the Python app manually in ISPmanager, or set DEPLOY_SSH_KEY"
    echo "    in deploy.env to let this script touch tmp/restart.txt over SSH."
fi
