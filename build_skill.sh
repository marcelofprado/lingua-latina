#!/usr/bin/env bash
# Zip the self-contained skill (for manual upload in Claude > Customize > Skills).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p dist
find skills -name __pycache__ -type d -prune -exec rm -r {} +
rm -f dist/latin-morphology-skill.zip
(cd skills && zip -qr ../dist/latin-morphology-skill.zip latin-morphology)
echo "dist/latin-morphology-skill.zip"
