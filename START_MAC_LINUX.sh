#!/usr/bin/env sh
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
  echo 'Open http://localhost:8000 in a browser (Ctrl+C to exit)'
  python3 -m http.server 8000
else
  echo 'Python 3 not installed. Open index.html in your browser.'
fi
