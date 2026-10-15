#!/usr/bin/env python3
"""HWP 붙여넣기용 HTML에 글자 크기 툴바·본문 복사 버튼·표 폭 고정 스크립트를 넣는다.

사용: python3 add_toolbar.py 파일.html [파일2.html ...]
- 이미 들어 있으면 최신 조각으로 바꾼다(여러 번 실행해도 안전).
- 예전 표 폭 스크립트(resizeTableByTextLength)는 지운다. 새 스크립트가 표 폭을 대신 잡는다.
"""
import re
import sys
from pathlib import Path

SNIPPET = (Path(__file__).resolve().parent.parent / 'templates' / 'toolbar.html').read_text(encoding='utf-8').strip()
BLOCK = re.compile(r'<!--hwp-toolbar:start-->.*?<!--hwp-toolbar:end-->\s*', re.S)
OLD_RESIZE = re.compile(r'<script>(?:(?!</script>).)*resizeTableByTextLength(?:(?!</script>).)*</script>\s*', re.S)
BODY = re.compile(r'<body[^>]*>', re.I)


def inject(path: Path) -> str:
    html = path.read_text(encoding='utf-8')
    html = BLOCK.sub('', html)
    html = OLD_RESIZE.sub('', html)
    m = BODY.search(html)
    if not m:
        return 'skip (body 없음)'
    html = html[:m.end()] + '\n' + SNIPPET + '\n' + html[m.end():]
    path.write_text(html, encoding='utf-8')
    return 'ok'


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        print(f'{inject(Path(arg))}\t{arg}')
