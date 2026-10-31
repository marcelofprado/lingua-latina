#!/usr/bin/env bash
# Zip the self-contained skill for manual upload in Claude (Customize > Skills).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p dist
rm -f dist/latin-morphology-skill.zip
(cd skills && zip -qr ../dist/latin-morphology-skill.zip latin-morphology -x '*/__pycache__/*')
echo "dist/latin-morphology-skill.zip"
