#!/usr/bin/env bash
set -euo pipefail

PORT="8080"
NO_OPEN="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-open)
      NO_OPEN="true"
      shift
      ;;
    ''|*[!0-9]*)
      echo "Unknown argument: $1" >&2
      echo "Usage: ./scripts/preview.sh [port] [--no-open]" >&2
      exit 1
      ;;
    *)
      PORT="$1"
      shift
      ;;
  esac
done

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DOCS_DIR="$(cd -- "${SCRIPT_DIR}/../docs" && pwd)"
URL="http://localhost:${PORT}/"

open_url() {
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "${URL}" >/dev/null 2>&1 &
  elif command -v open >/dev/null 2>&1; then
    open "${URL}" >/dev/null 2>&1 &
  elif command -v cmd.exe >/dev/null 2>&1; then
    cmd.exe /c start "" "${URL}" >/dev/null 2>&1
  else
    echo "Could not auto-open browser. Open ${URL} manually."
  fi
}

if [[ "${NO_OPEN}" != "true" ]]; then
  open_url
fi

if command -v python3 >/dev/null 2>&1; then
  cd "${DOCS_DIR}"
  exec python3 -m http.server "${PORT}"
elif command -v python >/dev/null 2>&1; then
  cd "${DOCS_DIR}"
  exec python -m http.server "${PORT}"
else
  echo "Python is required for local preview. Install Python 3 and rerun." >&2
  exit 1
fi