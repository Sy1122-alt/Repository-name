# -*- coding: utf-8 -*-
import pymupdf, re, json
from collections import defaultdict

# ---- 1. 提取四级词 ----
SRC = r'D:\BaiduNetdiskDownload\单词\大学英语四级词汇完整版带音标-乱序版.pdf'
d = pymupdf.open(SRC)
rows = []
for page in d:
    for t in page.find_tables().tables:
        for row in t.extract():
            if not row or len(row) < 4:
                continue
            seq, word, phon, mean = (row[0] or '').strip(), (row[1] or '').strip(), (row[2] or '').strip(), (row[3] or '').strip()
            if not word or seq in ('序号', '') or re.fullmatch(r'\d+', word):
                continue
            if not re.search(r'[A-Za-z]', word):
                continue
            rows.append([word, phon, mean])
print('四级原始行:', len(rows))

seen = {}
for w, ph, m in rows:
    key = w.lower()
    if key not in seen:
        seen[key] = [w, ph, m]
cet = sorted(seen.values(), key=lambda x: x[0].lower())
print('四级去重后:', len(cet))

# ---- 2. 读专升本词库（原始提取独立文件）----
zsb = json.load(open(r'D:\专升本学习\错题本\_zsb_words.json', encoding='utf-8'))
print('专升本词数:', len(zsb))

zsb_map = {w[0].lower(): w for w in zsb}
cet_map = {w[0].lower(): w for w in cet}

# ---- 3. 对比标记 ----
common = sorted(set(zsb_map) & set(cet_map))
cet_only = sorted(set(cet_map) - set(zsb_map))
zsb_only = sorted(set(zsb_map) - set(cet_map))
print('通用:', len(common), '四级独有:', len(cet_only), '专升本独有:', len(zsb_only))

# ---- 4. 生成合并词库 [word, phon, pos, mean, tag] ----
merged = []
for key in common:
    z = zsb_map[key]
    c = cet_map[key]
    word, phon, pos, mean = z[:4]
    if not phon:
        phon = c[1]
    if not mean:
        mean = c[2]
    phon = re.sub(r'\s+', ' ', phon).strip()
    mean = re.sub(r'\s+', ' ', mean).strip()
    merged.append([word, phon, pos, mean, '通用'])
for key in cet_only:
    w = cet_map[key]
    raw_mean = re.sub(r'\s+', ' ', w[2]).strip()
    pos = ''
    m = re.match(r'^([a-z]{1,4})\.\s*(.*)$', raw_mean)
    if m:
        pos = m.group(1)
        mean = m.group(2)
    else:
        mean = raw_mean
    merged.append([w[0], w[1], pos, mean, '四级'])
for key in zsb_only:
    z = zsb_map[key]
    merged.append([z[0], z[1], z[2], z[3], '专升本'])

merged.sort(key=lambda x: x[0].lower())
print('合并后总词数:', len(merged))
json.dump(merged, open(r'D:\专升本学习\错题本\_words_merged.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ---- 5. 生成单词本.md（带来源标记）----
groups = defaultdict(list)
for word, phon, pos, mean, tag in merged:
    letter = word[0].upper()
    if not ('A' <= letter <= 'Z'):
        letter = '#'
    groups[letter].append((word, phon, pos, mean, tag))

def fmt(e):
    word, phon, pos, mean, tag = e
    parts = ['- ' + word]
    if phon:
        parts.append('[' + phon + ']')
    if pos:
        parts.append(pos + '.')
    parts.append(mean if mean else '（释义待补）')
    parts.append('【' + tag + '】')
    return ' '.join(parts)

lines = []
lines.append('# 英语 · 单词本')
lines.append('')
lines.append('> 专升本 + 四级 合并词表（共 **%d** 词）。来源：《英语单词完整版》PDF +《大学英语四级词汇完整版》PDF。' % len(merged))
lines.append('> 每条词尾 `【通用】`=专升本与四级都覆盖；`【四级】`=仅四级新增；`【专升本】`=仅专升本词表。')
lines.append('> 运行 `错题本/build.py` 生成《单词本.html》与《生词本.html》；修改词条后重新运行即可重建。')
lines.append('> 词条格式：`- 单词 [音标] 词性. 释义 【来源】`')
lines.append('')
lines.append('---')
lines.append('')
total = 0
for letter in sorted(groups):
    items = sorted(groups[letter], key=lambda x: x[0].lower())
    lines.append('## %s（%d 词）' % (letter, len(items)))
    lines.append('')
    for e in items:
        lines.append(fmt(e))
        total += 1
    lines.append('')

out = r'D:\专升本学习\英语\错题集\单词本.md'
with open(out, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('写入:', out, '总词条:', total)
