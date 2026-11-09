#!/usr/bin/env bash
# Run ON the EC2 host (via SSH or EC2 Instance Connect):
#   curl -fsSL https://raw.githubusercontent.com/marcelofprado/lingua-latina/server/deploy/install-on-server.sh -o install.sh
#   bash install.sh latin.diodorus.com.br
# Builds and starts the latin-morph container (127.0.0.1:8010), configures nginx
# for the domain and, if certbot is installed, issues the TLS certificate.
set -euo pipefail
DOMAIN="${1:-latin.diodorus.com.br}"
DIR="$HOME/lingua-latina"
REPO="https://github.com/marcelofprado/lingua-latina"

command -v docker >/dev/null || { echo "docker not found"; exit 1; }
if [ -d "$DIR/.git" ]; then
  git -C "$DIR" fetch -q origin server && git -C "$DIR" checkout -q server && git -C "$DIR" reset -q --hard origin/server
else
  git clone -q -b server "$REPO" "$DIR"
fi
cd "$DIR"
docker compose -f deploy/docker-compose.yml up -d --build
echo "waiting for the service..."
for i in $(seq 1 40); do curl -fs http://127.0.0.1:8010/health && break; sleep 3; done
echo

if command -v nginx >/dev/null; then
  CONF=/etc/nginx/conf.d/latin.conf
  [ -d /etc/nginx/conf.d ] || CONF=/etc/nginx/sites-enabled/latin.conf
  sed "s/latin.example.com/$DOMAIN/" deploy/nginx-latin.conf | sudo tee "$CONF" >/dev/null
  sudo nginx -t && sudo systemctl reload nginx
  echo "nginx: $DOMAIN -> 127.0.0.1:8010"
  if command -v certbot >/dev/null; then
    sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --redirect \
      --register-unsafely-without-email || echo "certbot failed: check that DNS for $DOMAIN points to this host"
  else
    echo "certbot not installed: terminate TLS on the ALB, or install certbot and run: sudo certbot --nginx -d $DOMAIN"
  fi
else
  echo "nginx not found on the host: point your proxy/ALB target at port 8010"
fi
echo "Test: curl -s https://$DOMAIN/health"
