#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
docker compose up -d --wait --wait-timeout 900
printf '\nOdoo: http://aadhi:9999  Login: team / team1234\n'
