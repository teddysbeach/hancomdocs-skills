#!/usr/bin/env python3
"""구성도(추진조직표) → HWP 붙여넣기용 <table> 생성기.

위에서 아래로 갈라지는 트리형 조직도를 '칸 병합 + 빈 칸 테두리 연결선'으로 그린다.
HWP는 <colgroup>과 CSS 폭을 무시하므로, 열 폭은 맨 위 '눈금 행'의 width 속성으로 잡고
테두리·배경은 셀마다 인라인 style로 넣어 어떤 템플릿에 끼워도 모양이 유지되게 한다.

사용:
  python3 orgchart.py spec.json            # <table> 조각을 stdout으로
  python3 orgchart.py spec.json -o out.html --page   # 단독 미리보기 HTML

spec.json 형식 (references/org-chart.md 참고):
{
  "width": 560, "font_pt": 10,
  "root": {"title": "사업 총괄", "sub": "업체A · 총괄책임자"},
  "side": {"title": "외부 자문", "sub": "기관A"},          # 선택
  # 노드에 "slots": 2 를 주면 자식이 없어도 상자 폭을 2칸 이상으로 넓힘
  "sections": [
    {"nodes": [
      {"title": "과제1", "sub": "업체A",
       "children": [{"title": "업체B", "sub": "개발"}, {"title": "업체C", "sub": "검증"}],
       "detail": "프로젝트A\\n1차년도 완료"}]},        # detail: 자식 아래 요약 상자(선택)
    {"band": "▼ 공통 지원 ▼", "nodes": [...]}
  ]
}
"""
import argparse, html, json, sys

LINE = '1.5px solid {c}'


def esc(s):
    return html.escape(s or '', quote=False).replace('\n', '<br/>')


def label(n):
    t = f'<b>{esc(n.get("title"))}</b>'
    if n.get('sub'):
        t += '<br/>' + esc(n['sub'])
    return t


class Grid:
    """열 N개짜리 행을 쌓는다. 빈 칸은 {'t':윗선, 'r':오른선}, 상자는 (시작열, 끝열, html, 종류)."""

    def __init__(self, n, colors, font_pt):
        self.n, self.c, self.pt = n, colors, font_pt
        self.rows = []

    def gap(self, vert=(), top=()):
        cells = [{'t': False, 'r': False} for _ in range(self.n + 1)]
        for b in vert:
            if 1 <= b <= self.n:
                cells[b]['r'] = True
        for a, b in top:
            for k in range(max(1, a), min(self.n, b) + 1):
                cells[k]['t'] = True
        self.rows.append(('gap', cells, []))

    def boxes(self, items):
        self.rows.append(('box', None, items))

    def _box_style(self, kind):
        bg = {'head': self.c['head'], 'band': self.c['band']}.get(kind, '#FFFFFF')
        return (f'border:1px solid {self.c["line"]};background:{bg};text-align:center;'
                f'vertical-align:middle;padding:4px 1px;font-size:{self.pt}pt;word-break:keep-all')

    def render(self, widths):
        out = ['<tr style="height:1px">' + ''.join(
            f'<td width="{w}" style="width:{w}px;height:1px;padding:0;border:none;font-size:1pt;line-height:1pt"></td>'
            for w in widths) + '</tr>']
        line = LINE.format(c=self.c['line'])
        for kind, cells, items in self.rows:
            tds, col = [], 1
            if kind == 'box':
                starts = {s: (s, e, tx, k) for s, e, tx, k in items}
                while col <= self.n:
                    if col in starts:
                        s, e, tx, k = starts[col]
                        tag = 'th' if k == 'head' else 'td'
                        tds.append(f'<{tag} colspan="{e - s + 1}" style="{self._box_style(k)}">{tx}</{tag}>')
                        col = e + 1
                        continue
                    s = col
                    while col < self.n and (col + 1) not in starts:
                        col += 1
                    tds.append(f'<td colspan="{col - s + 1}" style="border:none;padding:0"></td>')
                    col += 1
                out.append('<tr>' + ''.join(tds) + '</tr>')
            else:
                while col <= self.n:
                    s, t = col, cells[col]['t']
                    while not cells[col]['r'] and col < self.n and cells[col + 1]['t'] == t:
                        col += 1
                    st = 'border:none;padding:0;height:10px;font-size:1pt;line-height:1pt;'
                    if t:
                        st += f'border-top:{line};'
                    if cells[col]['r']:
                        st += f'border-right:{line};'
                    span = f' colspan="{col - s + 1}"' if col > s else ''
                    tds.append(f'<td{span} style="{st}"></td>')
                    col += 1
                out.append('<tr style="height:10px">' + ''.join(tds) + '</tr>')
        return out


def build(spec):
    colors = {'head': '#EEEEEE', 'band': '#D9D9D9', 'line': '#000000'}
    colors.update(spec.get('colors', {}))
    secs = spec['sections']
    slots_of = lambda node: max(node.get('slots', 1), len(node.get('children', [])))
    S = max(sum(slots_of(nd) for nd in sec['nodes']) for sec in secs)
    N = 4 * S                                   # 슬롯 = [빈][칸][칸][빈]
    g = Grid(N, colors, spec.get('font_pt', 10))
    C = 2 * S                                   # 전체 중심 경계(열 C와 C+1 사이)

    # 각 구간의 노드 배치: 슬롯 범위 → 상자 열·중심 경계
    layout = []
    for sec in secs:
        s_used = sum(slots_of(nd) for nd in sec['nodes'])
        off = 2 * (S - s_used)                  # 슬롯이 적은 구간은 가운데로
        k, nodes = 0, []
        for nd in sec['nodes']:
            a, b = k, k + slots_of(nd)
            L, R = off + 4 * a, off + 4 * b     # 열 L+1..R 이 이 노드의 슬롯 영역
            nk = len(nd.get('children', []))
            ko = (b - a - nk) // 2                # slots가 자식보다 많으면 자식을 가운데로
            kids = [(L + 4 * (ko + j) + 2, L + 4 * (ko + j) + 3, L + 4 * (ko + j) + 2) for j in range(nk)]
            nodes.append({'nd': nd, 'box': (L + 2, R - 1), 'c': (L + R) // 2, 'kids': kids})
            k = b
        layout.append(nodes)

    # 맨 위 상자(+ 옆 상자)
    items = [(C - 2, C + 3, label(spec['root']), 'head')]
    if spec.get('side') and N - 5 > C + 4:
        items.append((N - 5, N, label(spec['side']), 'box'))
    g.boxes(items)

    def fan(centers, from_c):
        """from_c 에서 내려와 centers 로 갈라지는 연결선 2행."""
        g.gap(vert=[from_c])
        lo, hi = min(centers + [from_c]), max(centers + [from_c])
        g.gap(vert=centers, top=[(lo + 1, hi)] if hi > lo else [])

    for si, (sec, nodes) in enumerate(zip(secs, layout)):
        centers = [x['c'] for x in nodes]
        if si == 0:
            fan(centers, C)
        else:
            prev = [x['c'] for x in layout[si - 1]]
            g.gap(vert=prev)
            g.boxes([(2 if S > 1 else 1, N - 1 if S > 1 else N, esc(sec.get('band', '')), 'band')])
            g.gap(vert=centers)
        g.boxes([(x['box'][0], x['box'][1], label(x['nd']), 'head') for x in nodes])
        if any(x['kids'] for x in nodes):
            g.gap(vert=centers)
            vert, top = [], []
            for x in nodes:
                kc = [kd[2] for kd in x['kids']] or [x['c']]
                vert += kc
                if len(kc) > 1:
                    top.append((min(kc) + 1, max(kc)))
            g.gap(vert=vert, top=top)
            kid_boxes = []
            for x in nodes:
                for (s, e, _), kn in zip(x['kids'], x['nd'].get('children', [])):
                    kid_boxes.append((s, e, label(kn), 'box'))
            g.boxes(kid_boxes)
        if any(x['nd'].get('detail') for x in nodes):
            vert, top = [], []
            for x in nodes:
                kc = [kd[2] for kd in x['kids']] or [x['c']]
                vert += kc
            g.gap(vert=vert)
            for x in nodes:
                kc = [kd[2] for kd in x['kids']] or [x['c']]
                if len(kc) > 1:
                    top.append((min(kc) + 1, max(kc)))
            g.gap(vert=centers, top=top)
            g.boxes([(x['box'][0], x['box'][1], esc(x['nd']['detail']), 'box')
                     for x in nodes if x['nd'].get('detail')])

    # 열 폭: 빈 열은 좁게, 칸 열은 나머지를 나눔
    W, gw = spec.get('width', 560), spec.get('gap_px', 8)
    gap_cols = {c for c in range(1, N + 1) if c % 4 in (0, 1)}
    cw = (W - gw * len(gap_cols)) // (N - len(gap_cols))
    widths = [gw if c in gap_cols else cw for c in range(1, N + 1)]
    rows = g.render(widths)
    return (f'<table data-orgchart="1" style="border-collapse:collapse;border:none;table-layout:fixed;width:{sum(widths)}px">\n'
            + '\n'.join(rows) + '\n</table>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('spec')
    ap.add_argument('-o', '--out')
    ap.add_argument('--page', action='store_true', help='단독 미리보기 HTML로 감싼다')
    a = ap.parse_args()
    spec = json.load(open(a.spec, encoding='utf-8'))
    tbl = build(spec)
    if a.page:
        tbl = ('<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>'
               '*{font-family:"맑은고딕","Malgun Gothic",sans-serif;line-height:160%;margin:0;word-break:keep-all}'
               'body{max-width:' + str(spec.get('width', 560) + 40) + 'px;margin:20px auto}'
               '</style></head><body>\n' + tbl + '\n</body></html>\n')
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(tbl)
    else:
        sys.stdout.write(tbl)


if __name__ == '__main__':
    main()
