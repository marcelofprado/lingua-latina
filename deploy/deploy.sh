#!/usr/bin/env bash
# Deploy latin-morph to the diodorus-1 EC2 host over SSH.
#   HOST=ec2-user@<ip-or-dns> KEY=~/.ssh/diodorus.pem DOMAIN=latin.example.com ./deploy/deploy.sh
set -euo pipefail
: "${HOST:?set HOST=user@host}"
KEY_OPT=${KEY:+-i "$KEY"}
DOMAIN=${DOMAIN:-}
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TAR=/tmp/latin-morph.tgz
tar -C "$ROOT" --exclude='.git' --exclude='__pycache__' --exclude='dist' -czf "$TAR" \
    Dockerfile .dockerignore requirements-server.txt skills server deploy
scp $KEY_OPT "$TAR" "$HOST:/tmp/latin-morph.tgz"
ssh $KEY_OPT "$HOST" bash -s -- "$DOMAIN" <<'REMOTE'
set -euo pipefail
DOMAIN="$1"
mkdir -p ~/latin-morph && tar -xzf /tmp/latin-morph.tgz -C ~/latin-morph
cd ~/latin-morph
docker compose -f deploy/docker-compose.yml up -d --build
for i in $(seq 1 30); do curl -fs http://127.0.0.1:8010/health && break; sleep 2; done
echo
if [ -n "$DOMAIN" ] && [ -d /etc/nginx/conf.d ]; then
  sed "s/latin.example.com/$DOMAIN/" deploy/nginx-latin.conf | sudo tee /etc/nginx/conf.d/latin.conf >/dev/null
  sudo nginx -t && sudo systemctl reload nginx
  echo "nginx configured for $DOMAIN"
fi
REMOTE
echo "Done. Test: curl -s http://${DOMAIN:-<host>}/health"
