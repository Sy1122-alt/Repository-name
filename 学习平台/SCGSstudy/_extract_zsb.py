# -*- coding: utf-8 -*-
# 从专升本 PDF 重新提取原始词库（独立于单词本.md，避免合并污染）
import pymupdf, re, json
from collections import Counter

SRC = r'D:\BaiduNetdiskDownload\英语单词完整版_20230720102733.pdf'
d = pymupdf.open(SRC)

line_re = re.compile(
    r'^\s*([A-Za-z][A-Za-z\'\-]*(?:[²³]|\([0-9A-Za-z]+\))?)\s*'
    r'(?:\[([^\]]*)\]\s*)?'
    r'((?:[a-z]{1,4}\.)[\s.,]*)'
    r'(.+)$'
)
line_re2 = re.compile(
    r'^\s*([A-Za-z][A-Za-z\'\-]*(?:[²³]|\([0-9A-Za-z]+\))?)\s*\[([^\]]*)\]\s*(.+)$'
)
POS_OK = {'n','v','vt','vi','a','adj','ad','adv','prep','conj','num','art','pron','int','aux','abbr','pl','modal'}

entries = []
for page in d:
    W = page.rect.width
    lines = []
    for block in page.get_text('dict', sort=False)['blocks']:
        if block.get('type') != 0:
            continue
        for line in block.get('lines', []):
            x0, y0, x1, y1 = line['bbox']
            txt = ''.join(sp['text'] for sp in line['spans']).strip()
            if not txt:
                continue
            col = 0 if x0 < W / 2 else 1
            lines.append((col, y0, x0, txt))
    lines.sort(key=lambda t: (t[0], round(t[1], 1), t[2]))
    cur = None
    cur_col = None
    for col, y0, x0, ln in lines:
        if re.match(r'^(专升本|专升本3500词正序版|[A-Z]\s*$)', ln):
            continue
        m = line_re.match(ln)
        if m:
            if cur:
                entries.append(cur)
            word, phon, pos, mean = m.group(1), (m.group(2) or '').strip(), m.group(3).strip().rstrip('.').strip(), m.group(4).strip()
            cur = [word, phon, pos, mean]
            cur_col = col
            continue
        m2 = line_re2.match(ln)
        if m2:
            if cur:
                entries.append(cur)
            cur = [m2.group(1), m2.group(2).strip(), '', m2.group(3).strip()]
            cur_col = col
            continue
        if cur is not None and col == cur_col:
            if re.match(r'^[A-Za-z][A-Za-z\'\-]*\s*\[', ln):
                continue
            cur[3] = (cur[3] + ' ' + ln).strip()
if cur:
    entries.append(cur)

# 词性补全
pos_lead = re.compile(r'^((?:[a-z]{1,4}\.){1,3})\s*(.*)$')
for e in entries:
    if not e[2]:
        m = pos_lead.match(e[3])
        if m:
            toks = m.group(1).rstrip('.').split('.')
            ok = [t for t in toks if t in POS_OK]
            if ok:
                e[2] = ok[0]
                e[3] = m.group(2).strip()
    if e[2] not in POS_OK:
        e[2] = ''

seen = {}
for e in entries:
    w = e[0].lower()
    if w not in seen:
        seen[w] = e
dedup = sorted(seen.values(), key=lambda x: x[0].lower())

json.dump(dedup, open(r'D:\专升本学习\错题本\_zsb_words.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('专升本原始词:', len(dedup))
c = Counter(x[2] for x in dedup)
print('词性:', c.most_common(6))
