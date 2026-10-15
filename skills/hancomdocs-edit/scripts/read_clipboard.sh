#!/bin/bash
# 한컴독스에서 cmd+a, cmd+c로 복사한 클립보드를 평문과 칸 구조 표시본으로 저장한다.
# 사용법: read_clipboard.sh <출력 경로 접두어>  → <접두어>.txt, <접두어>.cell.txt
set -e
OUT="${1:?출력 경로 접두어를 주세요}"
sleep 1
pbpaste > "$OUT.txt"
osascript -e 'the clipboard as «class HTML»' 2>/dev/null \
  | sed 's/«data HTML//; s/»$//' | xxd -r -p > "$OUT.html" || true
python3 - "$OUT" <<'PY'
import re, html, sys
out = sys.argv[1]
try:
    s = open(out + '.html', encoding='utf-8', errors='ignore').read()
except FileNotFoundError:
    s = ''
s = re.sub(r'<style.*?</style>', '', s, flags=re.S)
s = re.sub(r'<br\s*/?>', '⏎', s)
s = re.sub(r'</p>', '¶\n', s)
t = html.unescape(re.sub(r'<[^>]+>', '', s))
t = re.sub(r'[ \t]+', ' ', t)
open(out + '.cell.txt', 'w', encoding='utf-8').write(t)
PY
echo "평문: $(wc -c < "$OUT.txt") bytes → $OUT.txt"
echo "칸 구조: $OUT.cell.txt (⏎=칸 안 줄바꿈, ¶=문단 끝)"
