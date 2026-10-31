#!/usr/bin/env bash
# Assemble the self-contained Claude Skill and zip it into dist/.
set -euo pipefail
cd "$(dirname "$0")"
SK=skill/latin-morphology
mkdir -p "$SK/scripts" dist
rm -rf "$SK/scripts/latin_morph"
cp -r latin_morph "$SK/scripts/"
find "$SK" -name __pycache__ -type d -prune -exec rm -r {} +
cp LICENSE "$SK/LICENSE"
(cd skill && rm -f ../dist/latin-morphology-skill.zip && zip -qr ../dist/latin-morphology-skill.zip latin-morphology)
echo "dist/latin-morphology-skill.zip"
