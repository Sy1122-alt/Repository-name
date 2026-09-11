# -*- coding: utf-8 -*-
"""
通用错题本构建工具
==================
一次运行，为三个学科生成各自的复习页（含英语单词卡）、题库刷题页，并生成统一入口 index.html。

用法：
    python "D:\\专升本学习\\SCGSstudy\\build.py"

数据源约定（各学科错题集目录内）：
    错题本.md  —— 错题记录（三科通用格式，见各科文件顶部说明）
    单词卡.md  —— 英语生词表（仅英语使用）
    题库.md    —— 题库（各学科根目录，用于生成题库刷题页）

生成的产物：
    各学科错题集/复习页.html
    英语错题集/单词卡.html
    各学科/题库页.html
    SCGSstudy/index.html
"""
import json
import re
import pathlib
from datetime import date
import sys
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gaoshu_kaodian import guess_kaodian

# 项目根目录（本文件位于 错题本 子目录）
BASE = pathlib.Path(__file__).resolve().parent
ROOT = BASE.parent

SUBJECTS = [
    {
        "name": "计算机",
        "label": "计算机",
        "dir": ROOT / "计算机" / "错题集",
        "mode": "math",     # 计算机进制、编码等题目也会使用 LaTeX 公式
        "color": "#9BBBF4",
        "icon": "CS",
        "desc": "进制 / 操作系统 / Office / 网络 / 数据结构",
    },
    {
        "name": "高数",
        "label": "高等数学",
        "dir": ROOT / "高数" / "错题集",
        "mode": "math",     # math：支持 KaTeX 渲染 $...$ / $$...$$
        "color": "#94D8C3",
        "icon": "Σ",
        "desc": "极限 / 导数 / 积分 / 微分方程 / 级数",
    },
    {
        "name": "英语",
        "label": "英语",
        "dir": ROOT / "英语" / "错题集",
        "mode": "normal",
        "color": "#C9A7E8",
        "icon": "EN",
        "desc": "语法 / 阅读 / 词汇错题 + 单词本 / 生词本",
    },
]

# 解析时关心的字段（其余字段原样保留给前端）
FIELD_KEYS = ("章节", "题型", "题目", "选项", "答案", "解析", "知识点",
              "错因", "日期", "状态", "错误次数", "最近复习", "优先级")


def read_clean(path):
    """读取并去掉 HTML 注释块（示例/占位说明不参与解析）。"""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return text


def parse_md(path, prefix="Q"):
    """把 错题本.md 解析为条目列表。prefix 决定条目前缀（Q 或 W）。"""
    if not path.exists():
        return []
    text = read_clean(path)
    items = []
    blocks = re.split(r"^##\s*%s-(\d+)\s*$" % prefix, text, flags=re.M)
    for i in range(1, len(blocks), 2):
        qid = blocks[i].strip()
        body = blocks[i + 1]
        item = {"id": qid}
        last_key = None
        for line in body.splitlines():
            line = line.strip()
            m = re.match(r"^-\s*([^:：]+)\s*[:：]\s*(.*)$", line)
            if m:
                key = m.group(1).strip()
                val = m.group(2).strip()
                last_key = key
                if key == "选项":
                    # 按 "A." 字母+点分段，避免选项内容里的 "/"（如"显示/打印"）被误切
                    opts = []
                    for p in re.split(r"(?=[A-H]\.)", val):
                        p = p.strip().rstrip("/／").strip()
                        if p:
                            opts.append(p)
                    if opts:
                        item["options"] = opts
                else:
                    item[key] = val
            elif line and last_key and last_key not in ("选项",):
                # 续行：追加到上一个文本字段（支持多行题目、解析等）
                item[last_key] = (item.get(last_key, "") + "\n" + line).strip()
        item.setdefault("状态", "待复习")
        item.setdefault("章节", "未分类")
        # 数字字段规范化
        for k in ("错误次数", "优先级"):
            if k in item:
                try:
                    item[k] = int(item[k])
                except ValueError:
                    item[k] = 0
        item.setdefault("错误次数", 0)
        if item.get("题目") or item.get("单词"):
            items.append(item)
    items.sort(key=lambda x: int(x["id"]) if x["id"].isdigit() else 0)
    return items


def _field_from_block(block, field):
    """读取质量检查需要的 Markdown 字段。"""
    match = re.search(
        r"(?ms)^-\s*%s\s*[:：]\s*(.*?)(?=^-\s*[^:：]+\s*[:：]|\Z)"
        % re.escape(field),
        block,
    )
    return match.group(1).strip() if match else ""


def _normalize_question(value):
    return re.sub(r"\s+", "", value or "").casefold()


def quality_check():
    """扫描三科错题源和题库，返回可展示的质量报告。"""
    report = {
        "generatedAt": date.today().isoformat(),
        "subjects": [],
        "issues": [],
        "summary": {"errors": 0, "warnings": 0, "questions": 0},
    }

    def add_issue(subject, level, source, message, item=""):
        report["issues"].append({
            "subject": subject, "level": level, "source": source,
            "item": item, "message": message,
        })
        report["summary"]["errors" if level == "error" else "warnings"] += 1

    for sub in SUBJECTS:
        subject = sub["name"]
        book = sub["dir"] / "错题本.md"
        tiku = sub["dir"].parent / "题库.md"
        book_clean = re.sub(r"<!--.*?-->", "", book.read_text(encoding="utf-8") if book.exists() else "", flags=re.S)
        book_blocks = list(re.finditer(r"^##\s*Q-(\d+)\s*$", book_clean, re.M))
        ids = [m.group(1) for m in book_blocks]
        for qid in sorted({x for x in ids if ids.count(x) > 1}):
            add_issue(subject, "error", "错题本.md", "错题序号重复", "Q-" + qid)
        for index, header in enumerate(book_blocks):
            end = book_blocks[index + 1].start() if index + 1 < len(book_blocks) else len(book_clean)
            block = book_clean[header.start():end]
            qid = "Q-" + header.group(1)
            for field in ("章节", "题目", "答案", "解析"):
                if not _field_from_block(block, field):
                    add_issue(subject, "error", "错题本.md", "缺少字段：" + field, qid)
            if not _field_from_block(block, "错因"):
                add_issue(subject, "warning", "错题本.md", "尚未记录错因", qid)

        tiku_items = parse_tiku(tiku, subject)
        report["summary"]["questions"] += len(tiku_items)
        seen = {}
        for item in tiku_items:
            label = str(item.get("id") or "未编号")
            fingerprint = _normalize_question(item.get("题目")) + "|" + _normalize_question("/".join(item.get("选项") or []))
            if fingerprint and fingerprint in seen:
                add_issue(subject, "warning", "题库.md", "题目与另一题重复", label)
            elif fingerprint:
                seen[fingerprint] = label
            if not item.get("题目"):
                add_issue(subject, "error", "题库.md", "缺少题目", label)
            if not item.get("答案") or item.get("答案") == "见解析":
                add_issue(subject, "error", "题库.md", "缺少答案", label)
            if not item.get("解析") or item.get("解析") == "（本题未附解析）":
                add_issue(subject, "warning", "题库.md", "缺少解析", label)
            options = item.get("选项") or []
            answer = str(item.get("答案") or "").strip()
            if options and item.get("题型") in ("单选", "多选"):
                letters = set(re.findall(r"[A-H]", answer.upper()))
                if not letters or any(ord(letter) - 65 >= len(options) for letter in letters):
                    add_issue(subject, "error", "题库.md", "选项数量与答案不匹配", label)
            if item.get("章节") == DEFAULT_CHAPTER:
                # 综合卷类专题（真题/模拟卷/专项/操作题/简答/Office 综合）归"综合"属预期，不提示
                _tp = item.get("专题") or ""
                if any(k in _tp for k in ("真题", "模拟卷", "专项", "操作", "简答", "Office")):
                    continue
                add_issue(subject, "warning", "题库.md", "未能自动归类章节", label)

        report["subjects"].append({
            "name": subject, "errorBook": len(book_blocks),
            "questionBank": len(tiku_items),
        })
    return report


def js_safe(data):
    s = json.dumps(data, ensure_ascii=False, indent=1)
    return s.replace("</", "<\\/")


# ============================================================
# 题库解析（各学科根目录 题库.md → 刷题页数据）
# ============================================================
# 题库题目块格式（题库.md 中）：
#   **真题 1.** 题干
#   - A. xx　B. xx　C. xx　D. xx        （选项可在一行用全角空格/斜杠分隔）
#   - **答案：D**　解析：xxx
#   - 来源：xxx
# 判断题组：**练习 20-29（判断题）** 后跟 "N. 语句（ **对**，说明）" 行，会拆成多道单选。
# 英语阅读：**Passage（标题）**：…… 后跟 **真题 N.** 题目，Passage 文本作为"材料"并入后续题目。

# 专题 → 错题本章节 映射（与各科《错题本.md》章节预设一致）
CHAPTER_MAP = {
    "高数": {
        "极限": "01-函数与极限",
        "极限与连续": "01-函数与极限",
        "一元微分": "02-导数与微分",
        "一元函数微分学": "02-导数与微分",
        "一元积分": "04-不定积分",
        "多元函数": "07-多元函数微积分",
        "无穷级数": "08-无穷级数",
        "常微分方程": "06-微分方程",
        "线性代数": "09-线性代数",
    },
    "计算机": {
        "进制转换": "01-计算机基础知识",
        "编码": "01-计算机基础知识",
        "判断对错": "01-计算机基础知识",
        "计算机基础知识": "01-计算机基础知识",
        "基础知识": "01-计算机基础知识",
        "Windows": "02-操作系统",
        "操作系统": "02-操作系统",
        "Word": "03-Word 文字处理",
        "Excel": "04-Excel 电子表格",
        "PowerPoint": "05-PowerPoint 演示文稿",
        "网络": "06-计算机网络",
        "Internet": "06-计算机网络",
        "安全": "07-信息安全与病毒",
        "多媒体": "07-信息安全与病毒",
        "数据库": "10-程序设计基础",
        "数据结构": "09-数据结构与算法",
    },
    "英语": {
        "词汇与语法": "02-语法",
        "词汇辨析": "01-词汇与词组",
        "阅读理解": "03-阅读理解",
        "完形": "04-完形填空",
        "时态": "02-语法",
        "从句": "02-语法",
        "非谓语": "02-语法",
        "虚拟": "02-语法",
        "情态": "02-语法",
        "交际": "02-语法",
        "写作模板": "06-写作",
    },
    "高数": {
        "极限": "01-函数与极限",
        "极限与连续": "01-函数与极限",
        "一元微分": "02-导数与微分",
        "一元函数微分学": "02-导数与微分",
        "导数": "02-导数与微分",
        "中值": "03-中值定理与导数应用",
        "导数应用": "03-中值定理与导数应用",
        "一元积分": "04-不定积分",
        "一元函数积分学": "04-不定积分",
        "不定积分": "04-不定积分",
        "定积分": "05-定积分及其应用",
        "定积分及其应用": "05-定积分及其应用",
        "积分": "04-不定积分",
        "多元函数": "07-多元函数微积分",
        "多元函数与二重积分": "07-多元函数微积分",
        "二重积分": "07-多元函数微积分",
        "无穷级数": "08-无穷级数",
        "级数": "08-无穷级数",
        "常微分方程": "06-微分方程",
        "微分方程": "06-微分方程",
        "线性代数": "09-线性代数",
    },
}
DEFAULT_CHAPTER = "99-综合"

# 计算机简答题：按题目关键词细分章节
SUBJECT_CHAPTER_RULES = {
    "计算机": [
        (["进制", "二进制", "十进制", "八进制", "十六进制", "转换为"], "01-计算机基础知识"),
        (["存储空间", "汉字", "U 盘", "可存放"], "01-计算机基础知识"),
        (["子网", "掩码"], "06-计算机网络"),
        (["输入又是输出", "触摸屏", "截图", "PrintScreen"], "02-操作系统"),
        (["数据库", "SQL", "关系模型", "大数据", "DESC", "GROUP BY", "查询结果"], "10-程序设计基础"),
        (["ENIAC", "电子管", "补码", "浮点数", "尾数", "无符号", "总线"], "01-计算机基础知识"),
        (["物联网", "云计算", "数字素养", "图灵", "二分查找"], "09-数据结构与算法"),
        (["主频", "数据模型", "DeepSeek", "编码", "采样", "量化", "ASCII", "GB2312", "GBK", "UTF-8"], "01-计算机基础知识"),
        (["IP 地址", "域名", "网络空间", "网络伦理"], "06-计算机网络"),
        (["虚拟内存", "外存", "回收站", "进程"], "02-操作系统"),
        (["冒泡排序", "程序执行"], "09-数据结构与算法"),
        (["栈", "队列", "LIFO", "FIFO"], "09-数据结构与算法"),
        (["BIOS", "回收站", "进程", "虚拟内存", "外存容量"], "02-操作系统"),
        (["网站", "IP 地址", "域名", "网络空间", "网络伦理"], "06-计算机网络"),
        (["数据模型", "DeepSeek"], "10-程序设计基础"),
        (["Word 中", "Word 页码", "字体为加粗"], "03-Word 文字处理"),
        (["声音", "幻灯片备注", "大纲", "讲义"], "05-PowerPoint 演示文稿"),
        (["word", "Word"], "03-Word 文字处理"),
        (["excel", "Excel"], "04-Excel 电子表格"),
        (["ppt", "PPT", "演示"], "05-PowerPoint 演示文稿"),
        (["网络", "拓扑"], "06-计算机网络"),
        (["病毒", "信息", "安全"], "07-信息安全与病毒"),
        (["冯·诺依曼", "五大部件", "组成"], "01-计算机基础知识"),
        (["文件", "操作系统", "windows", "Windows"], "02-操作系统"),
    ],
}
# 英语简答/练习：按知识点关键词细分章节
SUBJECT_CHAPTER_RULES["英语"] = [
    (["president", "minutes'", "coat", "author", "must have", "together with", "due to", "No sooner", "Poor .* she"], "02-语法"),
    (["语法", "时态", "从句", "虚拟", "倒装", "非谓语", "主谓一致"], "02-语法"),
    (["词汇", "词组", "短语", "搭配"], "01-词汇与词组"),    (["阅读"], "03-阅读理解"),
    (["完形"], "04-完形填空"),
    (["翻译", "汉译", "英译"], "05-翻译"),
    (["写作", "作文"], "06-写作"),
]
# 高数：按知识点关键词细分章节
SUBJECT_CHAPTER_RULES["高数"] = [
    (["偏导", "多元", "二重积分", "二元函数", "f(x,y", "矩形区域", "dz=", "dz|", "dz}{", "\\partial", "\\iint"], "07-多元函数微积分"),
    (["空间", "平面方程", "点到平面", "距离", "对称点", "yOz", "xOy", "xOz", "方向向量", "法向量", "梯度", "球面"], "07-多元函数微积分"),
    (["微分方程", "通解", "满足 y(0)", "y'=2y", "衰变", "冷却"], "06-微分方程"),
    (["中值", "罗尔", "拉格朗日", "不等式证明", "不等式", "恒等式", "至少有一个"], "03-中值定理与导数应用"),
    (["最值", "最大", "最小", "用料", "容积", "利润", "边际", "造价", "费用"], "03-中值定理与导数应用"),
    (["极值", "拐点", "凹凸", "单调", "渐近线", "极小值", "极大值", "凸区间", "凹区间"], "03-中值定理与导数应用"),
    (["面积", "围成", "旋转体"], "05-定积分及其应用"),
    (["一元函数微分学", "导数", "切线", "单调", "极值"], "02-导数与微分"),
    (["一元函数积分学", "不定积分", "定积分"], "04-不定积分"),
    (["级数", "敛散", "麦克劳林", "展开式", "幂级数", "\\sum"], "08-无穷级数"),
    (["极限", "间断", "无穷小", "无穷大", "等价", "奇函数", "f[f", "f\\left", "f(x-", "f(x+", "f(2x", "f(3x", "f(a", "f(\\ln", "函数值", "复合函数"], "01-函数与极限"),
    (["\\lim", "\\to"], "01-函数与极限"),
    (["导数", "微分", "切线", "法线", "求导", "参数方程", "相切", "f'", "y'=", "dy=", "\\frac{dy}{dx}", "\\dfrac{dy}{dx}"], "02-导数与微分"),
    (["不定积分", "原函数", "\\int"], "04-不定积分"),
    (["行列式", "矩阵", "线性方程", "向量", "特征值", "方阵", "可逆", "\\begin{pmatrix}", "\\begin{vmatrix}"], "09-线性代数"),
    (["定义域", "极限", "可导"], "01-函数与极限"),
]
def guess_chapter(subject, topic, title, text):
    """根据专题/标题/正文推断错题本「章节」字段。"""
    cmap = CHAPTER_MAP.get(subject, {})
    if topic in cmap:
        return cmap[topic]
    # 子串匹配（专题名可能带修饰词，如"一元函数积分学"↔"一元积分"）
    for key, chap in cmap.items():
        if key in topic or topic in key:
            return chap
    # 计算机简答、英语等按正文关键词细分
    for rules in (SUBJECT_CHAPTER_RULES.get(subject, []),):
        for kws, chap in rules:
            hay = topic + " " + title + " " + text
            if any(k in hay for k in kws):
                return chap
    return DEFAULT_CHAPTER


def split_options(line):
    """把 '- A. xx　B. xx …' 行拆成选项列表。"""
    body = line[1:].strip() if line.startswith("-") else line.strip()
    # 按 "A." 等字母+点 开头分段
    opts = []
    # 替换全角空格为普通空格再切分
    body = body.replace("　", " ")
    parts = re.split(r"(?=[A-H]\.)", body)
    for p in parts:
        p = p.strip()
        m = re.match(r"^([A-H])\.\s*(.*)$", p, flags=re.S)
        if m:
            opt = m.group(2).strip()
            # 去掉选项末尾的"/"分隔符
            opt = re.sub(r'\s*/\s*$', '', opt).strip()
            opts.append(opt)
    return opts


# 模拟卷等综合卷题目：按题干内容关键词归入知识点专题（专题名不体现来源）
TOPIC_CONTENT_RULES = {
    "高数": [
        (["微分方程", "通解", "可分离变量", "一阶线性", "特征方程", "(y')", "y'+", "y''-"], "常微分方程"),
        ([r"\iint", "二重积分", "二次积分", "偏导", "多元", "全微分", "dz", "d\theta", "f(x,y", r"\partial", "空间", "平面方程", "点到平面", "到平面", "对称点", "梯度", "球面", "直线", "两平面", "过点", "切平面", "法平面", "方向导数"], "多元函数与二重积分"),
        ([r"\int_", "定积分", "变上限", "旋转体", "围成", "广义积分", "反常积分"], "定积分及其应用"),
        (["极值", "极小值", "极大值", "拐点", "凹凸", "单调", "渐近线", "最值", "最大", "最小", "中值", "罗尔", "拉格朗日", "实根", "证明", "围建"], "导数应用"),
        (["导数", "微分", "切线", "法线", "求导", "参数方程", "f'", "y'=", "dy=", "y'", "y''", "y''" "'", "dy}{dx"], "一元函数微分学"),
        (["级数", "敛散", "麦克劳林", "幂级数", r"\sum", "正项级数", "交错级数", "循环小数"], "无穷级数"),
        ([r"\lim", "极限", "间断", "无穷小", "无穷大", "等价", "数列", "收敛子列", "定义域", "反函数", "奇函数", "偶函数", "连续区间"], "极限与连续"),
        ([r"\int", "不定积分", "原函数"], "一元函数积分学"),
        (["行列式", "矩阵", "向量", "特征值", "线性方程", "可逆", "方阵", "|A|", "A^{-1}", "相似", "(AB)", r"\begin{pmatrix}", r"\begin{vmatrix}", "秩"], "线性代数"),
    ],
    "计算机": [
        (["进制", "二进制", "十进制", "八进制", "十六进制", "转换为"], "进制转换"),
        (["ASCII", "GB2312", "GBK", "UTF-8", "编码", "汉字", "存储", "单位", "KB", "MB", "GB", "字节", "位"], "编码、单位与存储"),
        (["Word", "文字处理", "文档", "段落", "字体", "页码", "页眉"], "Word 文字处理"),
        (["Excel", "电子表格", "单元格", "工作表", "函数", "公式"], "Excel 电子表格"),
        (["PowerPoint", "PPT", "演示文稿", "幻灯片", "放映", "讲义"], "PowerPoint 演示文稿"),
        (["网络", "IP", "域名", "拓扑", "子网", "协议", "Internet", "上网", "浏览器"], "网络与Internet"),
        (["病毒", "安全", "加密", "防火墙", "木马", "黑客", "杀毒"], "安全与多媒体"),
        (["数据库", "SQL", "关系模型", "大数据", "数据模型"], "数据库与新技术"),
        (["栈", "队列", "二叉树", "排序", "算法", "数据结构", "链表", "查找"], "数据结构与算法"),
        (["操作系统", "Windows", "进程", "文件", "虚拟内存", "回收站", "窗口", "桌面", "任务栏"], "操作系统"),
    ],
    "英语": [
        (["完形", "Cloze"], "完形填空"),
        (["Passage", "passage", "阅读", "短文"], "阅读理解"),
        (["翻译", "汉译", "英译", "Translation"], "翻译"),
        (["写作", "作文", "Writing"], "写作"),
    ],
}


def topic_from_content(subject, item):
    """综合卷题目按题干内容关键词推断知识点专题；兜底：英语→词汇与语法，其余→综合。"""
    hay = (item.get("题目") or "") + " " + (item.get("材料") or "")
    for kws, tp in TOPIC_CONTENT_RULES.get(subject, []):
        if any(k in hay for k in kws):
            return tp
    if subject == "英语":
        return "词汇与语法"
    if subject == "计算机":
        return "计算机基础知识"
    return "综合"


def clean_topic_title(raw):
    """`## ` 二级标题 → 专题名。
    例：'专题一 · 进制转换（高频必考）'→'进制转换'；'2023年真题（四川省专升本统考·计算机基础）'→'2023年真题'；
        '库课模拟卷-计算机-基础1（单选）'→'库课模拟卷-计算机-基础1'（单选/多选两行自动合并）；
        '库课模拟卷·基础检测卷（一）改编版·高等数学'→'库课模拟卷·基础检测卷'（同卷多套合并）；
        '自编计算机题（Windows操作系统）'→'自编计算机题（Windows操作系统）'（自编分类括号保留）。
    """
    t = re.sub(r"^专题[^\s\u00b7]*\s*[\u00b7]?\s*", "", raw).strip()
    if not t:
        return "综合"
    # 特例：专题一名统一（"词汇与语法结构"≡"词汇与语法"）
    if t.startswith("词汇与语法结构") or t.startswith("语法单选"):
        return "词汇与语法"
    # 特例：真题年份统一（旧专题名与新真题段合并）
    if t.startswith("2022 四川专升本真题"):
        return "2022年真题"
    if t.startswith("2025 真题客观题"):
        return "2025年真题"
    # 高数库课模拟卷：去卷号括号（一）（二）…与"改编版·高等数学"后缀（兼容旧标题）
    t = re.sub(r"[（(][一二三四五六七八九十]+[）)]", "", t)
    t = re.sub(r"改编版·高等数学$", "", t)
    # 去其余括号修饰（年份说明/单选多选/高频必考等）
    t = re.sub(r"[（(].*$", "", t).strip()
    return t or "综合"


def parse_tiku(path, subject):
    """解析学科根目录《题库.md》为题目列表（用于刷题页）。"""
    if not path.exists():
        return []
    text = read_clean(path)
    items = []
    topic = "综合"
    content_mode = False   # 模拟卷等综合卷标题后：题目按题干内容归类
    content_topic = None   # 标注段强制专题（如模拟卷（阅读）→"阅读理解"）
    material = []          # 阅读材料累积
    passage_text = []      # 完形填空完整原文累积
    is_cloze_passage = False
    cur = None

    def flush():
        nonlocal cur, topic, content_mode, content_topic
        if cur is not None and not cur.get("判断题组"):
            cur.pop("_pending", None)
            cur.pop("_proof_mode", None)
            if cur.get("材料") or cur.get("题目") or cur.get("选项"):
                if content_mode:
                    cur["专题"] = content_topic or topic_from_content(subject, cur)
                else:
                    cur["专题"] = topic
                # 推断考点（仅高数）
                if subject == "高数" and not cur.get("考点"):
                    text_for_kd = cur.get("题目", "") + " " + cur.get("材料", "") + " " + cur.get("解析", "") + " " + cur.get("答案", "")
                    cur["考点"] = guess_kaodian(subject, cur.get("题目", ""), text_for_kd)
                items.append(cur)
            cur = None
        elif cur is not None:
            cur = None

    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            continue
        # 附录标题：结束当前题目块，避免附录内容被吞进最后一题（必须在专题匹配之前）
        if s.startswith("## 附") or s.startswith("附："):
            flush()
            continue
        # 二级标题 → 专题边界（真题按年份、知识点按内容；库课模拟卷/模拟卷精选不设边界，题目按内容归类）
        mt = re.match(r"^##\s+(.+)$", s)
        if mt:
            flush()
            raw = mt.group(1)
            if "模拟卷" in raw or raw.startswith("自编"):
                # 模拟卷/自编：不设专题边界，题目按内容归类（专题名=知识点，不体现来源）
                content_mode = True
                content_topic = "阅读理解" if "（阅读）" in raw else None
                continue
            topic = clean_topic_title(raw)
            content_mode = False
            content_topic = None
            continue
        # 表格 / 引用说明 / 分隔线 / 代码块 跳过
        if s.startswith("|") or s.startswith(">") or s.startswith("---") or s.startswith("```"):
            continue
        # 阅读材料：**Passage（标题）**：内容
        mp = re.match(r"^\*\*Passage[（(]([^）)]*)[）)]\*\*(.*)$", s)
        if mp:
            # 去掉标题后的孤立中文/英文冒号
            body = mp.group(2).strip().lstrip("：:").strip()
            # 完形填空的Passage不附加为材料（题目本身已带句子上下文，附加完整原文会泄露答案）
            if "完形" in mp.group(1):
                material = []
                passage_text = [body] if body else []
                is_cloze_passage = True
            else:
                material = [body] if body else []
                passage_text = []
                is_cloze_passage = False
            continue
        # 完形Passage正文续行累积
        if is_cloze_passage and passage_text and not re.match(r"^\*\*(真题|练习|自编|多选|模拟卷|通关|站长错题)", s) and not s.lstrip().startswith("-") and not re.match(r"^#{1,4}\s", s):

            passage_text.append(s)
            continue
        # 材料累积（仅当正在读 Passage 时，且只累积不以"-"开头的正文续行，避免吞掉选项/答案/来源行）
        if material and not re.match(r"^\*\*(真题|练习|自编|多选|模拟卷|通关|站长错题)", s) and not s.lstrip().startswith("-") and not re.match(r"^#{1,4}\s", s):
            material.append(s)
            continue
        # 题目块起始（新编号格式：**类别-科目-题型-序号.** 或 **…-序号（判断组）.**）
        mb = re.match(r"^\*\*(真题|练习|自编|模拟卷|通关|站长错题)[\s\-]*(计算机|高数|英语)[\s\-]*(单选|多选|判断|填空|计算|证明|应用|简答)[\s\-]*(\d+)(?:-(\d+))?\s*(?:（判断组）)?[.、]?\s*\*\*\s*(.*)$", s)
        if mb:
            flush()
            qtype, subject_zh, qtype_zh, num, sub_num = mb.group(1), mb.group(2), mb.group(3), mb.group(4), mb.group(5)
            title = mb.group(6).strip().replace("**", "").strip()
            is_judge_group = ("（判断组）" in s or "判断题组" in s)
            # 独立判断题（题型段=判断）也识别为判断
            is_judge = is_judge_group or (qtype_zh == "判断")
            is_multi = (qtype_zh == "多选")
            mat = "\n".join(material) if material else ""
            passage = "\n".join(passage_text) if (is_cloze_passage and passage_text) else ""
            # 注意：不清空 material，使 Passage 材料持续附给该 Passage 下的所有题目
            cur = {
                "id": ("%s-%s-%s-%03d-%d" % (qtype, subject_zh, qtype_zh, int(num), int(sub_num))) if sub_num else ("%s-%s-%s-%03d" % (qtype, subject_zh, qtype_zh, int(num))),
                "来源": qtype,
                "专题": topic,
                "题型": qtype_zh,
                "材料": mat,
                "passage": passage,
                "题目": title,
                "选项": [],
                "答案": "",
                "解析": "",
                "考点": "",
            }
            if is_judge_group:
                cur["判断题组"] = True
            continue
        # 判断题组子题：N. 语句（ **对/错**，说明）
        if cur is not None and cur.get("判断题组"):
            mj = re.match(r"^\s*[-–]?\s*(\d+)\.\s*(.+?)\s*（\s*\*\*([对错])\*\*\s*[,，]?\s*([^）]*)）\s*$", s)
            if mj:
                item = {
                    "id": cur["id"] + "-" + mj.group(1),
                    "来源": cur["来源"],
                    "专题": cur["专题"],
                    "题型": "判断",
                    "材料": "",
                    "题目": mj.group(2).strip(),
                    "选项": ["对", "错"],
                    "答案": "对" if mj.group(3) == "对" else "错",
                    "解析": mj.group(4).strip(),
                }
                items.append(item)
                continue
        # 选项行（支持"- 选项：A. xx / B. xx"和"- A. xx"两种格式）
        if s.startswith("-") and (re.match(r"^-\s*选项\s*[:：]", s) or re.match(r"^-\s*[A-H]\.", s)):
            # 提取选项内容（去掉"- 选项："前缀）
            opt_body = re.sub(r"^-\s*选项\s*[:：]\s*", "", s)
            opts = split_options(opt_body)
            if opts and cur is not None:
                cur["_pending"] = None
                if cur.get("选项"):
                    # 已有选项则追加（处理每行一个选项的格式）
                    cur["选项"].extend(opts)
                else:
                    cur["选项"] = opts
            continue
        # 答案行（可能同行带解析，用全角空格/“解析”分隔）
        if cur is not None and ("答案" in s or "参考译文" in s or "参考范文" in s) and (s.startswith("- 答案") or s.startswith("- **答案") or s.startswith("- **参考译文") or s.startswith("- **参考范文")):
            body = s.lstrip("- ").strip()
            body = body.replace("**", "")
            m = re.match(r"^(?:答案(?:参考)?|参考译文|参考范文)(\s*[:：]?\s*)(.*)$", body, flags=re.S)
            if m:
                rest = m.group(2)
                # 答案与解析常同行："D**　解析：…"
                seg = re.split(r"[　 ]*解析\s*[:：]", rest)
                cur["答案"] = seg[0].strip()
                cur["_pending"] = "答案"
                if len(seg) > 1:
                    cur["解析"] = seg[1].strip()
            continue
        # 证明题格式（- **证明：** 开头，证明内容作为解析）
        if cur is not None and re.match(r"^-\s*\*{0,2}证明\s*[:：]", s):
            proof_text = re.sub(r"^-\s*\*{0,2}证明\s*[:：]\s*", "", s).replace("**", "").strip()
            cur["答案"] = "证明见解析"
            cur["解析"] = proof_text
            cur["_pending"] = None
            cur["_proof_mode"] = True
            continue
        # 证明题续行（以空格开头，且当前处于证明模式）
        if cur is not None and cur.get("_proof_mode") and s.startswith("  ") and not s.startswith("-"):
            cur["解析"] += "\n" + s.strip()
            continue
        # 独立解析行（题库同时支持“答案行同行解析”和单独的解析行）
        if cur is not None and re.match(r"^-\s*\*{0,2}解析\s*[:：]", s):
            cur["解析"] = re.sub(r"^-\s*\*{0,2}解析\s*[:：]\s*", "", s).replace("**", "").strip()
            cur["_pending"] = "解析"
            if cur.get("_proof_mode"):
                del cur["_proof_mode"]
            continue
        # 来源行
        if cur is not None and re.match(r"^-\s*来源\s*[:：]", s):
            cur["来源"] = re.sub(r"^-\s*来源\s*[:：]\s*", "", s).strip()
            cur["_pending"] = None
            continue
        # 标题行（#/##/###/#### 开头）：作为题目块的结束，flush当前题目，并清空阅读材料
        # （避免新章节的作文/翻译正文被误当作 Passage 材料累积）
        if re.match(r"^#{1,4}\s", s):

            if cur is not None:
                if cur.get("_proof_mode"):
                    del cur["_proof_mode"]
                cur["_pending"] = None
                flush()
                cur = None
            material = []
            passage_text = []
            is_cloze_passage = False
            continue
        # 其余行：若正处于答案/解析续行模式则续到对应字段，否则追加到题干（多行材料/续行）
        if cur is not None:
            if cur.get("_pending") in ("答案", "解析"):
                cur[cur["_pending"]] = (cur.get(cur["_pending"], "") + "\n" + s).strip()
            elif cur["题目"]:
                cur["题目"] += "\n" + s
            else:
                cur["题目"] = s
    flush()

    # 补齐章节映射 + 答案/解析缺省
    for it in items:
        text_for_chap = it["题目"] + " " + it["材料"] + " " + it["解析"] + " " + it["答案"]
        it["章节"] = guess_chapter(subject, it["专题"], it["题目"], text_for_chap)
        it["解析"] = it["解析"] or "（本题未附解析）"
        it["答案"] = it["答案"] or "见解析"
        if not it["选项"]:
            it["选项"] = []
            if it["题型"] == "单选":
                # 根据题目ID/标题关键词细分题型
                qid = it.get("id", "")
                title = it.get("题目", "")
                combined = qid + " " + title
                if "证明" in combined:
                    it["题型"] = "证明"
                elif "应用" in combined:
                    it["题型"] = "应用"
                elif "填空" in combined or re.search(r"_{2,}", title) or "＿" in title:
                    it["题型"] = "填空"
                elif re.search(r"计算[^机]", combined):
                    it["题型"] = "计算"
                else:
                    it["题型"] = "简答"
    return items


# ============================================================
# AI 学习助手（悬浮聊天 + 全局 AIAsk 供页面调用）
# ============================================================
AI_HTML = r"""
<div id="aiFab" title="AI 学习助手">🤖</div>
<div id="aiPanel" style="display:none;">
  <div id="aiHead"><span>AI 学习助手</span><button id="aiClose" aria-label="关闭">×</button></div>
  <div id="aiMsgs"></div>
  <div id="aiInputRow">
    <input id="aiInput" placeholder="问学习问题，或点题目的「AI讲题」…" maxlength="2000">
    <button id="aiSend">发送</button>
  </div>
</div>
<style>
#aiFab{position:fixed;right:16px;bottom:16px;width:52px;height:52px;border-radius:50%;
  background:linear-gradient(135deg,#4F7CF7,#6A5AF9);color:#fff;font-size:24px;
  display:flex;align-items:center;justify-content:center;cursor:pointer;z-index:9999;
  box-shadow:0 4px 14px rgba(79,124,247,.4);-webkit-tap-highlight-color:transparent;user-select:none;}
#aiPanel{position:fixed;right:16px;bottom:80px;width:min(360px,calc(100vw - 32px));height:min(480px,calc(100vh - 120px));
  background:#fff;border-radius:16px;box-shadow:0 8px 30px rgba(0,0,0,.18);z-index:9999;
  display:flex;flex-direction:column;overflow:hidden;border:1px solid #E4E3DD;}
#aiHead{background:linear-gradient(135deg,#4F7CF7,#6A5AF9);color:#fff;padding:10px 14px;
  font-size:14px;font-weight:600;display:flex;justify-content:space-between;align-items:center;}
#aiClose{background:rgba(255,255,255,.2);border:none;color:#fff;width:26px;height:26px;
  border-radius:50%;font-size:16px;line-height:1;cursor:pointer;}
#aiMsgs{flex:1;overflow-y:auto;padding:12px;background:#FAF9F6;display:flex;flex-direction:column;gap:8px;font-size:14px;}
.ai-msg{max-width:88%;padding:8px 11px;border-radius:12px;white-space:pre-wrap;word-break:break-word;line-height:1.55;}
.ai-user{align-self:flex-end;background:#4F7CF7;color:#fff;border-bottom-right-radius:4px;}
.ai-bot{align-self:flex-start;background:#fff;border:1px solid #E4E3DD;border-bottom-left-radius:4px;color:#1A1B1C;}
.ai-bot.err{color:#B44244;background:#FDF0EF;}
.ai-typing{color:#6B7280;font-style:italic;}
.ai-msg .ai-math{display:inline-block;margin:2px 2px;}
.ai-msg .ai-math-plain{font-family:Consolas,Monaco,monospace;font-size:0.92em;background:rgba(79,124,247,0.07);border-radius:4px;padding:0 4px;}
.ai-msg strong{font-weight:700;}
#aiInputRow{display:flex;gap:8px;padding:10px;border-top:1px solid #E4E3DD;background:#fff;}
#aiInput{flex:1;border:1px solid #D8D6CF;border-radius:10px;padding:8px 11px;font-size:14px;outline:none;min-width:0;}
#aiInput:focus{border-color:#4F7CF7;}
#aiSend{background:#4F7CF7;color:#fff;border:none;border-radius:10px;padding:0 16px;font-size:14px;cursor:pointer;font-weight:600;}
@media (max-width:480px){#aiPanel{right:8px;bottom:76px;width:calc(100vw - 16px);}}
</style>
<script>
(function(){
  var API="https://ai.scgsstudy.top";
  var fab=document.getElementById("aiFab");
  var panel=document.getElementById("aiPanel");
  var msgs=document.getElementById("aiMsgs");
  var input=document.getElementById("aiInput");
  var send=document.getElementById("aiSend");
  var close=document.getElementById("aiClose");
  if(!fab||!panel) return;
  var open=false;
  function toggle(force){
    open=(typeof force==="boolean")?force:!open;
    panel.style.display=open?"flex":"none";
    if(open&&input) input.focus();
  }
  fab.addEventListener("click",function(){ toggle(); });
  if(close) close.addEventListener("click",function(){ toggle(false); });
  function escAI(x){ return String(x).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
  function plainMath(x){
    return String(x)
      .replace(/\\frac\{([^{}]+)\}\{([^{}]+)\}/g,function(_,a,b){ return "("+a+"/"+b+")"; })
      .replace(/\\sqrt(\[[^{}\]]*\])?\{([^{}]+)\}/g,function(_,r,b){ return r?"("+b+")^(1/"+String(r).replace(/[\[\]]/g,"")+")":"√("+b+")"; })
      .replace(/\\dfrac\{([^{}]+)\}\{([^{}]+)\}/g,function(_,a,b){ return "("+a+"/"+b+")"; })
      .replace(/\\lim_?\{?([^{}]*)\}?/g,"lim→$1")
      .replace(/\\infty/g,"∞").replace(/\\to/g,"→").replace(/\\rightarrow/g,"→")
      .replace(/\\cdot/g,"·").replace(/\\times/g,"×").replace(/\\pm/g,"±")
      .replace(/\\le/g,"≤").replace(/\\ge/g,"≥").replace(/\\ne/g,"≠").replace(/\\approx/g,"≈")
      .replace(/\\left/g,"").replace(/\\right/g,"")
      .replace(/\\big|\\Big/g,"").replace(/\\([a-zA-Z]+)/g,"$1")
      .replace(/\\,/g," ").replace(/\\ /g," ")
      .replace(/[{}]/g,"");
  }
  function renderAI(text){
    if(!text) return "";
    var t=escAI(text);
    // 代码块先保护
    var codes=[];
    t=t.replace(/`([^`]*)`/g,function(_,c){ codes.push(c); return "\u0000C"+(codes.length-1)+"\u0000"; });
    function fmt(x,display){
      // 反转义：公式内容从已转义文本中提取，需还原 < > & 再给 KaTeX
      var raw=x.replace(/&lt;/g,"<").replace(/&gt;/g,">").replace(/&amp;/g,"&");
      try{
        if(typeof katex!=="undefined"&&katex.renderToString){
          return '<span class="ai-math">'+katex.renderToString(raw,{displayMode:display,throwOnError:false})+'</span>';
        }
      }catch(e){}
      return '<span class="ai-math-plain">'+plainMath(raw)+'</span>';
    }
    t=t.replace(/\$\$([\s\S]+?)\$\$/g,function(_,x){ return fmt(x,true); });
    t=t.replace(/\\\[([\s\S]+?)\\\]/g,function(_,x){ return fmt(x,true); });
    t=t.replace(/\$([^$\n]+?)\$/g,function(_,x){ return fmt(x,false); });
    t=t.replace(/\\\(([^\\]+?)\\\)/g,function(_,x){ return fmt(x,false); });
    t=t.replace(/\*\*([^*\n]+)\*\*/g,"<strong>$1</strong>");
    t=t.replace(/\u0000C(\d+)\u0000/g,function(_,i){
      return '<code style="background:rgba(0,0,0,0.06);border-radius:4px;padding:1px 5px;font-family:Consolas,Monaco,monospace;font-size:0.9em;color:#B44244;white-space:pre-wrap;word-break:break-all;">'+escAI(codes[+i]||"")+'</code>';
    });
    return t;
  }
  function append(role,text,cls){
    var d=document.createElement("div");
    d.className="ai-msg "+(role==="user"?"ai-user":"ai-bot")+(cls?" "+cls:"");
    if(role==="bot"&&!cls){ d.innerHTML=renderAI(text); }
    else{ d.textContent=text; }
    if(msgs) msgs.appendChild(d);
    if(msgs) msgs.scrollTop=msgs.scrollHeight;
    return d;
  }
  function ask(q,title){
    if(!q||!q.trim()) return;
    toggle(true);
    var finalQ=title?("【"+title+"】\n"+q):q;
    append("user",finalQ);
    var typing=append("bot","思考中…","ai-typing");
    fetch(API,{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({messages:[
        {role:"system",content:"你是四川专升本学习助手，擅长高等数学、计算机基础、大学英语。数学公式用LaTeX：行内 $...$，独立公式 $$...$$。解题铁律：1) 仔细审题，先明确题目问什么；2) 每一步计算必须准确，临界点、极值点等关键结果要代入验算；3) 只讲解与本题直接相关的内容，严禁添加与解题无关的表述（如多余的零点、无关性质、无关定理）；4) 术语严格准确：临界点=导数零点，零点=函数值为0的点，单调区间、极值、拐点等概念不可混用或并列；5) 不确定的地方明确说，不编造；6) 分点清晰，面向专升本考生，用中文。"},
        {role:"user",content:finalQ}
      ],max_tokens:700})})
      .then(function(r){
        if(!r.ok) return r.text().then(function(t){ throw new Error("服务返回 "+r.status+(t.length<150?": "+t:"")); });
        return r.json();
      })
      .then(function(j){
        var c=(j.choices&&j.choices[0]&&j.choices[0].message&&j.choices[0].message.content)||"(空回复)";
        typing.className="ai-msg ai-bot";
        typing.innerHTML=renderAI(c);
      })
      .catch(function(e){
        typing.className="ai-msg ai-bot err";
        typing.textContent="请求失败："+e.message;
      });
  }
  if(send) send.addEventListener("click",function(){ var v=input.value; if(v.trim()){ input.value=""; ask(v); } });
  if(input) input.addEventListener("keydown",function(e){ if(e.key==="Enter"&&!e.shiftKey){ e.preventDefault(); var v=input.value; if(v.trim()){ input.value=""; ask(v); } } });
  window.AIAsk=ask;
})();
</script>
"""


# ============================================================
# 投稿题目组件（模态框 + 浮动按钮 + 提交逻辑）
# 数据 POST 到 https://ai.scgsstudy.top/api/submit
# ============================================================
SUBMIT_HTML = r"""
<div id="subModal" style="display:none;position:fixed;inset:0;z-index:99990;background:rgba(15,23,42,0.55);backdrop-filter:blur(3px);justify-content:center;align-items:center;padding:16px;">
  <div style="background:#fff;border-radius:16px;max-width:560px;width:100%;max-height:92vh;overflow-y:auto;padding:22px 24px;box-sizing:border-box;box-shadow:0 20px 60px rgba(0,0,0,0.25);">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
      <div style="font-size:19px;font-weight:700;color:#1A1B1C;">📮 投稿题目</div>
      <div id="subClose" style="cursor:pointer;font-size:22px;color:#8a8f98;line-height:1;padding:2px 8px;">×</div>
    </div>
    <div style="display:flex;gap:8px;margin-bottom:16px;border-bottom:2px solid #f0f0f0;padding-bottom:0;">
      <button id="tabImage" type="button" style="flex:1;padding:10px;border:none;border-bottom:3px solid #4F7CF7;background:transparent;color:#4F7CF7;font-size:14px;font-weight:600;cursor:pointer;margin-bottom:-2px;">📷 上传图片</button>
      <button id="tabManual" type="button" style="flex:1;padding:10px;border:none;border-bottom:3px solid transparent;background:transparent;color:#6B7280;font-size:14px;font-weight:600;cursor:pointer;margin-bottom:-2px;">✏️ 手动填写</button>
    </div>

    <!-- ===== 上传图片模式 ===== -->
    <div id="panelImage">
      <div style="font-size:13px;color:#6B7280;margin-bottom:10px;line-height:1.6;">拍照或上传题目图片，管理员会识别题目并整理入库。</div>
      <div id="dropZone" style="border:2px dashed #d1d5db;border-radius:12px;padding:28px 16px;text-align:center;cursor:pointer;background:#fafafa;transition:all 0.2s;">
        <div style="font-size:34px;margin-bottom:6px;">📷</div>
        <div style="font-size:14px;color:#374151;font-weight:600;">点击选择图片 或 拖拽到这里</div>
        <div style="font-size:12px;color:#9ca3af;margin-top:4px;">支持 JPG/PNG，可多选，总大小≤18MB</div>
        <input type="file" id="fileInput" accept="image/*" multiple style="display:none;">
      </div>
      <div id="previewArea" style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;"></div>
      <div style="margin-top:14px;">
        <div style="font-size:13px;color:#374151;margin-bottom:5px;">科目 <span style="color:#e5484d;">*</span></div>
        <select id="subSubjectImg" style="width:100%;padding:9px 10px;border:1px solid #d1d5db;border-radius:9px;font-size:14px;background:#fff;">
          <option value="高数">高等数学</option>
          <option value="计算机">计算机基础</option>
          <option value="英语">大学英语</option>
        </select>
      </div>
      <div style="margin-top:12px;">
        <div style="font-size:13px;color:#374151;margin-bottom:5px;">备注（可选）</div>
        <textarea id="subNoteImg" rows="2" placeholder="如：2025年真题、第3页等" style="width:100%;padding:9px 10px;border:1px solid #d1d5db;border-radius:9px;font-size:14px;box-sizing:border-box;resize:vertical;font-family:inherit;line-height:1.5;"></textarea>
      </div>
    </div>

    <!-- ===== 手动填写模式 ===== -->
    <div id="panelManual" style="display:none;">
      <div style="font-size:13px;color:#6B7280;margin-bottom:14px;line-height:1.6;">手动填写题目信息，带 <span style="color:#e5484d;">*</span> 为必填。</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
        <div>
          <div style="font-size:13px;color:#374151;margin-bottom:5px;">科目 <span style="color:#e5484d;">*</span></div>
          <select id="subSubject" style="width:100%;padding:9px 10px;border:1px solid #d1d5db;border-radius:9px;font-size:14px;background:#fff;">
            <option value="高数">高等数学</option>
            <option value="计算机">计算机基础</option>
            <option value="英语">大学英语</option>
          </select>
        </div>
        <div>
          <div style="font-size:13px;color:#374151;margin-bottom:5px;">题型</div>
          <select id="subType" style="width:100%;padding:9px 10px;border:1px solid #d1d5db;border-radius:9px;font-size:14px;background:#fff;">
            <option value="单选">单选题</option>
            <option value="多选">多选题</option>
            <option value="判断">判断题</option>
            <option value="填空">填空题</option>
            <option value="简答">简答题</option>
            <option value="完形">完形填空</option>
            <option value="翻译">翻译题</option>
            <option value="其他">其他</option>
          </select>
        </div>
      </div>
      <div style="margin-bottom:12px;">
        <div style="font-size:13px;color:#374151;margin-bottom:5px;">题目内容 <span style="color:#e5484d;">*</span></div>
        <textarea id="subQuestion" rows="4" placeholder="题目内容，可含公式（用 $...$ 包裹）" style="width:100%;padding:9px 10px;border:1px solid #d1d5db;border-radius:9px;font-size:14px;box-sizing:border-box;resize:vertical;font-family:inherit;line-height:1.5;"></textarea>
      </div>
      <div style="margin-bottom:12px;">
        <div style="font-size:13px;color:#374151;margin-bottom:5px;">选项（每行一个，如 A.xxx）</div>
        <textarea id="subOptions" rows="3" placeholder="A. 选项一&#10;B. 选项二&#10;C. 选项三&#10;D. 选项四" style="width:100%;padding:9px 10px;border:1px solid #d1d5db;border-radius:9px;font-size:14px;box-sizing:border-box;resize:vertical;font-family:inherit;line-height:1.5;"></textarea>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
        <div>
          <div style="font-size:13px;color:#374151;margin-bottom:5px;">答案</div>
          <input id="subAnswer" type="text" placeholder="如：B 或 具体答案" style="width:100%;padding:9px 10px;border:1px solid #d1d5db;border-radius:9px;font-size:14px;box-sizing:border-box;" />
        </div>
        <div>
          <div style="font-size:13px;color:#374151;margin-bottom:5px;">题目来源</div>
          <input id="subSource" type="text" placeholder="如：真题2025 / 自编 / 机构" style="width:100%;padding:9px 10px;border:1px solid #d1d5db;border-radius:9px;font-size:14px;box-sizing:border-box;" />
        </div>
      </div>
      <div style="margin-bottom:16px;">
        <div style="font-size:13px;color:#374151;margin-bottom:5px;">备注（可选）</div>
        <textarea id="subNote" rows="2" placeholder="想补充的任何说明" style="width:100%;padding:9px 10px;border:1px solid #d1d5db;border-radius:9px;font-size:14px;box-sizing:border-box;resize:vertical;font-family:inherit;line-height:1.5;"></textarea>
      </div>
    </div>

    <div id="subMsg" style="font-size:13px;margin-bottom:12px;display:none;padding:9px 12px;border-radius:9px;line-height:1.5;"></div>
    <div style="display:flex;gap:10px;justify-content:flex-end;">
      <button id="subCancel" type="button" style="padding:10px 20px;border:1px solid #d1d5db;border-radius:10px;background:#fff;color:#374151;font-size:14px;cursor:pointer;">取消</button>
      <button id="subSend" type="button" style="padding:10px 22px;border:none;border-radius:10px;background:#4F7CF7;color:#fff;font-size:14px;font-weight:600;cursor:pointer;">提交投稿</button>
    </div>
  </div>
</div>
<button id="subFab" title="投稿题目" style="position:fixed;right:22px;bottom:96px;z-index:99970;width:50px;height:50px;border-radius:50%;border:none;background:linear-gradient(135deg,#4F7CF7,#8B5CF6);color:#fff;font-size:22px;cursor:pointer;box-shadow:0 6px 20px rgba(79,124,247,0.4);display:flex;align-items:center;justify-content:center;">📮</button>
<script>
(function(){
  var modal=document.getElementById('subModal'), fab=document.getElementById('subFab');
  var close=document.getElementById('subClose'), cancel=document.getElementById('subCancel'), send=document.getElementById('subSend');
  var msg=document.getElementById('subMsg'), subAPI="https://ai.scgsstudy.top/api/submit";
  if(!modal||!fab) return;

  // Tab 切换
  var tabImage=document.getElementById('tabImage'), tabManual=document.getElementById('tabManual');
  var panelImage=document.getElementById('panelImage'), panelManual=document.getElementById('panelManual');
  var currentTab='image';
  function switchTab(tab){
    currentTab=tab;
    if(tab==='image'){
      tabImage.style.color='#4F7CF7'; tabImage.style.borderBottomColor='#4F7CF7';
      tabManual.style.color='#6B7280'; tabManual.style.borderBottomColor='transparent';
      panelImage.style.display=''; panelManual.style.display='none';
    } else {
      tabManual.style.color='#4F7CF7'; tabManual.style.borderBottomColor='#4F7CF7';
      tabImage.style.color='#6B7280'; tabImage.style.borderBottomColor='transparent';
      panelManual.style.display=''; panelImage.style.display='none';
    }
  }
  if(tabImage) tabImage.addEventListener('click',function(){ switchTab('image'); });
  if(tabManual) tabManual.addEventListener('click',function(){ switchTab('manual'); });

  // 图片上传
  var fileInput=document.getElementById('fileInput'), dropZone=document.getElementById('dropZone'), previewArea=document.getElementById('previewArea');
  var uploadedImages=[]; // {filename, base64}
  function renderPreview(){
    if(!previewArea) return;
    previewArea.innerHTML='';
    uploadedImages.forEach(function(img,idx){
      var wrap=document.createElement('div');
      wrap.style.cssText='position:relative;width:80px;height:80px;border-radius:8px;overflow:hidden;border:1px solid #e5e7eb;';
      var im=document.createElement('img');
      im.src=img.base64; im.style.cssText='width:100%;height:100%;object-fit:cover;';
      var del=document.createElement('div');
      del.textContent='×'; del.style.cssText='position:absolute;top:2px;right:2px;width:20px;height:20px;background:rgba(0,0,0,0.6);color:#fff;border-radius:50%;font-size:14px;line-height:20px;text-align:center;cursor:pointer;';
      del.addEventListener('click',function(e){ e.stopPropagation(); uploadedImages.splice(idx,1); renderPreview(); });
      wrap.appendChild(im); wrap.appendChild(del);
      previewArea.appendChild(wrap);
    });
  }
  function handleFiles(files){
    if(!files||!files.length) return;
    var remaining=Array.prototype.slice.call(files);
    function processNext(){
      if(!remaining.length){ renderPreview(); return; }
      var file=remaining.shift();
      if(!file.type||file.type.indexOf('image/')!==0){ processNext(); return; }
      var reader=new FileReader();
      reader.onload=function(e){
        uploadedImages.push({filename:file.name||'image.jpg', base64:e.target.result});
        processNext();
      };
      reader.onerror=function(){ processNext(); };
      reader.readAsDataURL(file);
    }
    processNext();
  }
  if(dropZone&&fileInput){
    dropZone.addEventListener('click',function(){ fileInput.click(); });
    fileInput.addEventListener('change',function(e){ handleFiles(e.target.files); fileInput.value=''; });
    dropZone.addEventListener('dragover',function(e){ e.preventDefault(); dropZone.style.borderColor='#4F7CF7'; dropZone.style.background='#f0f4ff'; });
    dropZone.addEventListener('dragleave',function(){ dropZone.style.borderColor='#d1d5db'; dropZone.style.background='#fafafa'; });
    dropZone.addEventListener('drop',function(e){ e.preventDefault(); dropZone.style.borderColor='#d1d5db'; dropZone.style.background='#fafafa'; handleFiles(e.dataTransfer.files); });
  }

  function show(s){ modal.style.display=s?'flex':'none'; }
  function tip(t,ok){ if(!msg) return; msg.style.display='block'; msg.style.background=ok?'rgba(240,253,244,0.9)':'rgba(254,242,242,0.9)'; msg.style.color=ok?'#16a34a':'#dc2626'; msg.textContent=t; }
  window.openSubmit=function(subject){
    var s1=document.getElementById('subSubject'), s2=document.getElementById('subSubjectImg');
    if(subject){ var map={高数:'高数',计算机:'计算机',英语:'英语'}; if(map[subject]){ if(s1)s1.value=map[subject]; if(s2)s2.value=map[subject]; } }
    if(msg) msg.style.display='none';
    show(true);
  };
  fab.addEventListener('click',function(){
    var t=document.title||'';
    var guess='';
    if(t.indexOf('计算机')>=0){ guess='计算机'; }
    else if(t.indexOf('英语')>=0){ guess='英语'; }
    else if(t.indexOf('高数')>=0||t.indexOf('高等数学')>=0){ guess='高数'; }
    window.openSubmit(guess||undefined);
  });
  if(close) close.addEventListener('click',function(){ show(false); });
  if(cancel) cancel.addEventListener('click',function(){ show(false); });
  modal.addEventListener('click',function(e){ if(e.target===modal) show(false); });

  send.addEventListener('click',function(){
    if(currentTab==='image'){
      // 图片模式
      if(uploadedImages.length===0){ tip('请至少选择一张图片',false); return; }
      var subject=document.getElementById('subSubjectImg').value;
      var note=document.getElementById('subNoteImg').value.trim();
      send.disabled=true; send.textContent='上传中…';
      fetch(subAPI,{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({type:'image',subject:subject,note:note,images:uploadedImages})})
        .then(function(r){ return r.json().then(function(j){ return {ok:r.ok,j:j}; }); })
        .then(function(res){
          send.disabled=false; send.textContent='提交投稿';
          if(res.ok&&res.j.success){
            tip('图片上传成功！我们会尽快识别题目并审核入库。',true);
            uploadedImages=[]; renderPreview();
            document.getElementById('subNoteImg').value='';
            setTimeout(function(){ show(false); }, 1800);
          } else {
            tip((res.j&&res.j.error)||'上传失败，请重试',false);
          }
        })
        .catch(function(e){ send.disabled=false; send.textContent='提交投稿'; tip('网络错误：'+e.message,false); });
    } else {
      // 手动模式
      var subject=document.getElementById('subSubject').value;
      var qtype=document.getElementById('subType').value;
      var question=document.getElementById('subQuestion').value.trim();
      var options=document.getElementById('subOptions').value.trim();
      var answer=document.getElementById('subAnswer').value.trim();
      var source=document.getElementById('subSource').value.trim();
      var note=document.getElementById('subNote').value.trim();
      if(question.length<3){ tip('题目内容不能为空（至少3个字）',false); return; }
      send.disabled=true; send.textContent='提交中…';
      fetch(subAPI,{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({subject:subject,qtype:qtype,question:question,options:options,answer:answer,source:source,note:note})})
        .then(function(r){ return r.json().then(function(j){ return {ok:r.ok,j:j}; }); })
        .then(function(res){
          send.disabled=false; send.textContent='提交投稿';
          if(res.ok&&res.j.success){
            tip('投稿成功！管理员审核后会尽快入库，谢谢你的贡献。',true);
            document.getElementById('subQuestion').value='';
            document.getElementById('subOptions').value='';
            document.getElementById('subAnswer').value='';
            document.getElementById('subSource').value='';
            document.getElementById('subNote').value='';
            setTimeout(function(){ show(false); }, 1800);
          } else {
            tip((res.j&&res.j.error)||'提交失败，请重试',false);
          }
        })
        .catch(function(e){ send.disabled=false; send.textContent='提交投稿'; tip('网络错误：'+e.message,false); });
    }
  });
})();
</script>
"""


# ============================================================
# 复习页模板（三科共用；math 模式额外引入 KaTeX）
# ============================================================
REVIEW_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__LABEL__错题复习页</title>
<style>
:root{--accent:__COLOR__;--accent-d:#33475C;--text:#1A1B1C;--sub:#6B7280;--bg:#F4F3EE;--card:#FFFFFF;--border:#E4E3DD;}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent;}
body{font-family:'Roboto','PingFang SC','Segoe UI',Arial,sans-serif;background:var(--bg);color:var(--text);padding:16px;line-height:1.6;}
.wrap{max-width:760px;margin:0 auto;}
h1{font-size:20px;font-weight:700;margin-bottom:2px;}
.back{font-size:12px;color:var(--sub);text-decoration:none;display:inline-block;margin-bottom:6px;}
.sub{font-size:12px;color:var(--sub);margin-bottom:12px;}
.stats{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;}
.stat{flex:1 1 100px;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:9px 12px;}
.stat .n{font-size:18px;font-weight:700;}
.stat .l{font-size:11px;color:var(--sub);}
.stat.hot{border-color:var(--accent);}
.factor{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:10px 12px;margin-bottom:10px;font-size:12px;}
.factor .t{font-size:11px;color:var(--sub);margin-bottom:6px;}
.frow{display:flex;align-items:center;gap:8px;margin-bottom:4px;}
.frow .nm{flex:0 0 56px;color:var(--sub);}
.fbar{flex:1;height:10px;background:rgba(0,0,0,0.06);border-radius:5px;overflow:hidden;}
.fbar i{display:block;height:100%;background:var(--accent);}
.frow .ct{flex:0 0 34px;text-align:right;font-weight:600;}
.reason-tools{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:10px 0;font-size:12px;color:var(--sub);}
.reason-tools select,.reason-tools button{font-size:12px;padding:6px 8px;border:1px solid var(--border);border-radius:7px;background:#fff;color:var(--text);}
.reason-tools button{cursor:pointer;background:rgba(155,187,244,0.16);border-color:var(--accent);font-weight:600;}
.similar{border-top:1px solid var(--border);margin-top:10px;padding-top:10px;font-size:12px;color:var(--sub);}
.similar a{display:block;color:var(--accent-d);text-decoration:none;margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.toolbar{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px;}
.toolbar select,.toolbar button{font-size:13px;padding:7px 10px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--text);cursor:pointer;}
.toolbar button.primary{background:var(--accent-d);color:#fff;border-color:var(--accent-d);font-weight:600;}
.toolbar button.on{background:var(--accent);border-color:var(--accent);color:#1A1B1C;font-weight:600;}
.card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:16px;margin-bottom:12px;}
.meta{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-bottom:10px;}
.tag{font-size:11px;padding:2px 8px;border-radius:10px;background:var(--accent);color:#22304A;}
.tag.qid{background:rgba(0,0,0,0.06);color:var(--sub);}
.tag.review{background:rgba(234,102,104,0.14);color:#B44244;}
.tag.mastered{background:rgba(82,196,26,0.14);color:#3E8C13;}
.tag.err{background:rgba(250,173,20,0.18);color:#8A5B00;}
.tag.reason{background:rgba(155,187,244,0.18);color:#33509E;}
.qtext{font-size:15px;font-weight:600;margin-bottom:10px;white-space:pre-wrap;}
.opts{list-style:none;margin-bottom:10px;}
.opts li{font-size:13.5px;padding:10px 14px;border:1.5px solid var(--border);border-radius:10px;margin-bottom:8px;background:#FBFBF8;cursor:pointer;transition:all .18s ease;position:relative;user-select:none;-webkit-tap-highlight-color:transparent;}
.opts li:active{transform:scale(0.97);}
.opts li:hover{border-color:var(--accent);background:rgba(155,187,244,0.06);}
.opts li .ol{color:var(--sub);font-weight:600;}
.opts li .opt-letter{display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:6px;background:rgba(0,0,0,0.06);font-weight:700;font-size:12px;margin-right:8px;flex:0 0 auto;}
.opts li.sel{border-color:var(--accent-d);background:rgba(0,0,0,0.04);}
.opts li.sel .opt-letter{background:var(--accent-d);color:#fff;}
.opts li.right{border-color:#52C41A;background:rgba(82,196,26,0.12);animation:pulse .5s ease;}
.opts li.right .opt-letter{background:#52C41A;color:#fff;}
.opts li.wrong{border-color:#EA6668;background:rgba(234,102,104,0.12);animation:shake .4s ease;}
.opts li.wrong .opt-letter{background:#EA6668;color:#fff;}
@keyframes shake{0%,100%{transform:translateX(0);}20%{transform:translateX(-6px);}40%{transform:translateX(6px);}60%{transform:translateX(-4px);}80%{transform:translateX(4px);}}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(82,196,26,0.4);}70%{box-shadow:0 0 0 10px rgba(82,196,26,0);}100%{box-shadow:0 0 0 0 rgba(82,196,26,0);}}
.feedback{font-size:13px;font-weight:600;margin-bottom:8px;display:none;}
.feedback.ok{color:#3E8C13;}
.feedback.no{color:#B44244;}
.answer{display:none;border-left:3px solid var(--accent-d);background:rgba(155,187,244,0.10);padding:10px 12px;border-radius:0 8px 8px 0;margin-bottom:12px;font-size:13.5px;white-space:pre-wrap;}
.answer .k{font-weight:700;color:var(--accent-d);}
.btns{display:flex;gap:8px;flex-wrap:wrap;}
.btns button{font-size:13px;padding:8px 14px;border:1px solid var(--border);border-radius:8px;background:#fff;color:var(--text);cursor:pointer;}
.btns button.m{background:rgba(82,196,26,0.14);border-color:#52C41A;color:#3E8C13;font-weight:600;}
.btns button.u{background:rgba(234,102,104,0.12);border-color:#EA6668;color:#B44244;font-weight:600;}
.btns button.h{background:rgba(250,173,20,0.14);border-color:#FAAD14;color:#8A5B00;font-weight:600;}
.nav{display:flex;justify-content:space-between;gap:8px;margin-top:12px;}
.nav button{font-size:13px;padding:8px 14px;border:1px solid var(--border);border-radius:8px;background:var(--card);cursor:pointer;}
.empty{text-align:center;color:var(--sub);font-size:13px;padding:30px 10px;background:var(--card);border:1px dashed var(--border);border-radius:14px;}
.progress{height:6px;background:rgba(0,0,0,0.07);border-radius:3px;overflow:hidden;margin-bottom:10px;}
.progress i{display:block;height:100%;background:var(--accent-d);border-radius:3px;transition:width .2s;}
.hint{font-size:11.5px;color:var(--sub);margin-top:12px;line-height:1.7;}
.math-inline{display:inline-block;vertical-align:middle;}
/* 移动端适配 */
@media (max-width:480px){
  .toolbar select,.toolbar button{min-height:44px;font-size:14px;}
  .opts li{min-height:44px;display:flex;align-items:center;font-size:14px;padding:10px 12px;}
  .btns button{min-height:44px;font-size:14px;}
  .nav button{min-height:44px;font-size:14px;}
  .reason-tools select,.reason-tools button{min-height:40px;font-size:13px;}
  .similar a{min-height:40px;display:inline-flex;align-items:center;padding:8px 10px;}
  .qtext{font-size:16px;}
}
</style>
__KATEX_CSS__
</head>
<body>
<div class="wrap">
  <a class="back" href="__INDEX__">‹ 返回错题本总入口</a>
  <h1>__LABEL__ · 错题复习页</h1>
  <div class="sub">数据源：同目录《错题本.md》 · 由 SCGSstudy/build.py 生成 · 本地双击打开</div>

  <div class="stats">
    <div class="stat"><div class="n" id="nTotal">0</div><div class="l">总题数</div></div>
    <div class="stat"><div class="n" id="nReview">0</div><div class="l">待复习</div></div>
    <div class="stat"><div class="n" id="nMastered">0</div><div class="l">已掌握</div></div>
    <div class="stat"><div class="n" id="nRate">0%</div><div class="l">掌握率</div></div>
    <div class="stat hot"><div class="n" id="nDue">0</div><div class="l">今日到期</div></div>
  </div>
  <div class="progress"><i id="bar" style="width:0%"></i></div>

  <div class="factor" id="factorBox">
    <div class="t">错因分布（按错误次数统计）</div>
    <div id="factorList"></div>
  </div>
  <div class="factor" id="weakBox">
    <div class="t">薄弱点闭环</div>
    <div id="weakList">按错因记录后，这里会显示最需要回炉的章节。</div>
  </div>

  <div class="toolbar">
    <select id="selChapter"><option value="">全部章节</option></select>
    <select id="selStatus"><option value="">全部状态</option><option value="待复习">待复习</option><option value="已掌握">已掌握</option></select>
    <select id="selReason"><option value="">全部错因</option></select>
    <button id="btnShuffle" class="primary">随机抽题</button>
    <button id="btnOrder">顺序浏览</button>
    <button id="btnKey">易错题</button>
    <button id="btnDue">今日应复习</button>
    <button id="btnReset">重置进度</button>
    <button id="btnExportLocal">导出本地错题</button>
  </div>

  <div id="card"></div>
  <div class="hint">
    翻卡后选择「没记住 / 有点模糊 / 掌握」，系统会分别安排明天、3 天后或递进间隔后的复习。<br>
    易错题 = 错误次数 ≥ 2 的题（反复出错的薄弱题，考前重点攻克）。<br>
    更新：往《错题本.md》追加错题后，运行 SCGSstudy/build.py 重新生成。
  </div>
</div>

<script src="__KATEX_JS__"></script>
<script>
window.__DATA__ = __DATA_JSON__;
window.__TIKU_SIMPLE__ = __TIKU_SIMPLE_JSON__;
(function(){
  "use strict";
  var MATH = __MATH_MODE__;
  var ALL = (window.__DATA__||[]).slice();
  var TIKU = (window.__TIKU_SIMPLE__||[]).slice();
  // 合并本地存储的错题（手机APK/离线环境自动存入的）
  try{
    var _lkey="__SUBJECT___errorbook_local";
    var _local=JSON.parse(localStorage.getItem(_lkey)||"[]");
    // 题目规范化：去掉LaTeX标记和命令，统一纯文本后再匹配
    function normQ(s){
      return (s||"").replace(/\$([^$]*)\$/g, function(_,m){
        return m.replace(/\\to/g,"→").replace(/\\frac/g,"").replace(/\\[a-zA-Z]+/g,"").replace(/[{}]/g,"");
      }).replace(/\$/g,"").replace(/\\[a-zA-Z]+/g,"").replace(/[{}]/g,"").replace(/\s/g,"").slice(0,20);
    }
    // 本地错题先按id去重：同一id只保留一条，错误次数累计
    var _localMap={};
    _local.forEach(function(le){
      var id=le.id||("L-"+(le["题目"]||"").slice(0,20));
      if(_localMap[id]){
        _localMap[id]["错误次数"]=(_localMap[id]["错误次数"]||1)+(le["错误次数"]||1);
      }else{
        _localMap[id]=le;
        if(!_localMap[id]["错误次数"]) _localMap[id]["错误次数"]=1;
      }
    });
    _local=Object.values(_localMap);
    if(_local.length){
      _local.forEach(function(le){
        // 按id去重（不同题目即使答案相同也保留）
        var dup=ALL.find(function(it){ return it.id===le.id; });
        if(dup) return;
        // 本地错题无选项时，从题库数据按题目内容相似度补全选项
        if(!le["选项"] || !le["选项"].length){
          var qNorm=normQ(le["题目"]);
          var match=TIKU.find(function(it){
            var itNorm=normQ(it["题目"]);
            return itNorm&&qNorm&&(itNorm.indexOf(qNorm)>=0||qNorm.indexOf(itNorm)>=0);
          });
          if(match&&match["选项"]&&match["选项"].length) le["选项"]=match["选项"].slice();
        }
        ALL.push(le);
      });
    }
  }catch(e){}
  var storeKey = "__SUBJECT___cuowuji_v2";
  var statusMap = {};
  var revMap = {};
  var planMap = {};
  try{ var saved = JSON.parse(localStorage.getItem(storeKey)||"{}")||{}; statusMap=saved.st||{}; revMap=saved.rv||{}; planMap=saved.pm||{}; }catch(e){}
  try{ localStorage.removeItem("cuowuji_status_v1"); }catch(e){}
  function save(){ try{ localStorage.setItem(storeKey, JSON.stringify({st:statusMap,rv:revMap,pm:planMap})); }catch(e){} }
  function st(it){ return statusMap[it.id] || it["状态"] || "待复习"; }
  function setSt(id,v){ statusMap[id]=v; save(); }
  function lastRev(it){ return (planMap[it.id]&&planMap[it.id].last) || revMap[it.id] || it["最近复习"] || it["日期"] || ""; }
  function nextRev(it){ return (planMap[it.id]&&planMap[it.id].next) || ""; }
  function setRev(id,d){ revMap[id]=d; save(); }
  function daysBetween(d1,d2){
    try{
      var a=new Date(d1), b=new Date(d2);
      return Math.round((b-a)/86400000);
    }catch(e){ return 999; }
  }
  function today(){ var d=new Date(); return d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0"); }
  function addDays(base, days){ var d=new Date(base+"T00:00:00"); d.setDate(d.getDate()+days); return d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0"); }
  function isDue(it){
    var next=nextRev(it);
    return !next || daysBetween(next, today())>=0;
  }
  function schedule(it, grade){
    var old=planMap[it.id]||{}, level=Number(old.level)||0, days=1, status="待复习";
    if(grade==="hard"){ level=Math.max(1,level); days=3; }
    if(grade==="good"){ level=Math.min(level+1,4); days=[7,7,14,30,45][level]; status="已掌握"; }
    if(grade==="again"){ level=0; days=1; }
    var now=today();
    planMap[it.id]={last:now,next:addDays(now,days),level:level};
    setSt(it.id,status); setRev(it.id,now); save();
  }
  function recordReason(it, reason, increment){
    it["错因"]=reason;
    if(increment) it["错误次数"]=(Number(it["错误次数"])||0)+1;
    var payload={subject:"__SUBJECT__",id:it.id,reason:reason,increment:!!increment};
    if(location.protocol!=="http:" || location.hostname!=="127.0.0.1") return;
    fetch("/api/update-review",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)})
      .then(function(r){if(!r.ok)throw new Error("save");}).catch(function(){ });
  }
  function renderWeak(){
    var map={};
    ALL.forEach(function(it){
      var reason=it["错因"]||"未记录错因", chapter=it["章节"]||"未分类";
      var key=chapter+"｜"+reason;
      map[key]=(map[key]||0)+1;
    });
    var keys=Object.keys(map).sort(function(a,b){return map[b]-map[a];}).slice(0,5);
    $("weakList").innerHTML=keys.length?keys.map(function(k){return '<div class="frow"><span class="nm" style="flex-basis:180px">'+escHtml(k.replace("｜"," · "))+'</span><span class="ct">'+map[k]+' 次</span></div>';}).join(""): "暂无数据";
  }

  var list=[], idx=0, revealed=false;
  function $(id){ return document.getElementById(id); }

  // 渲染数学公式（KaTeX），失败则保留原文
  function escHtml(s){
    return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  }
  function renderMath(s){
    var t = escHtml(s).replace(/\\_/g,"_");
    // 保护反引号代码块（如Excel公式 $A$1、Shell $var），避免被KaTeX当数学公式
    var codes=[];
    t=t.replace(/`([^`]*)`/g, function(_,c){ codes.push(c); return "\u0000CODE"+(codes.length-1)+"\u0000"; });
    // 保护 Excel 单元格绝对/混合引用（$A$1、$A1、A$1），避免被KaTeX当数学公式
    var xls=[];
    t=t.replace(/\$[A-Z]{1,3}\$[0-9]{1,7}|\$[A-Z]{1,3}[0-9]{1,7}|[A-Z]{1,3}\$[0-9]{1,7}/g, function(m){ xls.push(m); return "\u0000XLS"+(xls.length-1)+"\u0000"; });
    function restoreXls(t){
      return t.replace(/\u0000XLS(\d+)\u0000/g, function(_,i){ return xls[+i]||""; });
    }
    function restore(t){
      return t.replace(/\u0000CODE(\d+)\u0000/g, function(_,i){
        return '<code style="background:rgba(0,0,0,0.06);border-radius:4px;padding:1px 6px;font-family:Consolas,Monaco,monospace;font-size:0.9em;color:#B44244;white-space:pre-wrap;word-break:break-all;">'+(codes[+i]||"")+'</code>';
      });
    }
    if(!MATH || typeof katex==="undefined") return restoreXls(restore(t));
    function unesc(x){ return x.replace(/&lt;/g,"<").replace(/&gt;/g,">").replace(/&amp;/g,"&").replace(/&quot;/g,'"'); }
    try{
      t = t.replace(/\$\$([\s\S]+?)\$\$/g, function(_,x){
        return '<div class="math-inline" style="margin:6px 0;">'+katex.renderToString(unesc(x),{displayMode:true,throwOnError:false})+'</div>';
      });
      t = t.replace(/\$([^$\n]+?)\$/g, function(_,x){
        return '<span class="math-inline">'+katex.renderToString(unesc(x),{displayMode:false,throwOnError:false})+'</span>';
      });
    }catch(e){}
    return restoreXls(restore(t));
  }

  var chapters=[], reasons=[];
  ALL.forEach(function(it){
    if(chapters.indexOf(it["章节"])<0) chapters.push(it["章节"]);
    if(it["错因"] && reasons.indexOf(it["错因"])<0) reasons.push(it["错因"]);
  });
  chapters.sort(); reasons.sort();
  chapters.forEach(function(c){ var o=document.createElement("option"); o.value=c; o.textContent=c; $("selChapter").appendChild(o); });
  reasons.forEach(function(r){ var o=document.createElement("option"); o.value=r; o.textContent=r; $("selReason").appendChild(o); });

  function filtered(){
    var c=$("selChapter").value, s=$("selStatus").value, r=$("selReason").value;
    return ALL.filter(function(it){
      if(c && it["章节"]!==c) return false;
      if(s && st(it)!==s) return false;
      if(r && it["错因"]!==r) return false;
      return true;
    });
  }
  function factorStat(){
    var map={}, total=0;
    ALL.forEach(function(it){
      var r=it["错因"]||"未分类"; map[r]=(map[r]||0)+1; total++;
    });
    var keys=Object.keys(map).sort(function(a,b){return map[b]-map[a];});
    return {map:map, keys:keys, total:total};
  }
  function renderFactor(){
    var f=factorStat(), box=$("factorList"), html="";
    if(!f.total){ box.innerHTML="<span style='color:var(--sub)'>暂无数据</span>"; return; }
    f.keys.forEach(function(k){
      var n=f.map[k], p=Math.round(n/f.total*100);
      html+='<div class="frow"><span class="nm">'+escHtml(k)+'</span><div class="fbar"><i style="width:'+p+'%"></i></div><span class="ct">'+n+'</span></div>';
    });
    box.innerHTML=html;
  }
  function renderStats(){
    var all=ALL.length, rev=0, mas=0, due=0;
    ALL.forEach(function(it){ st(it)==="已掌握" ? mas++ : rev++; if(isDue(it)) due++; });
    $("nTotal").textContent=all;
    $("nReview").textContent=rev;
    $("nMastered").textContent=mas;
    $("nRate").textContent=(all?Math.round(mas/all*100):0)+"%";
    $("bar").style.width=(all?Math.round(mas/all*100):0)+"%";
    $("nDue").textContent=due;
  }
  function show(){
    var box=$("card");
    if(!list.length){
      box.innerHTML='<div class="empty">当前筛选/模式下没有题目。<br>往《错题本.md》追加错题并运行 build.py 重新生成，或换个模式。</div>';
      return;
    }
    var it=list[idx];
    var answered=false;
    var cls=st(it)==="已掌握"?"mastered":"review";
    var label=st(it)==="已掌握"?"已掌握":"待复习";
    var meta='<span class="tag qid">Q-'+it.id+'</span><span class="tag">'+escHtml(it["章节"])+'</span><span class="tag '+cls+'">'+label+'</span>';
    if(it["题型"]) meta+='<span class="tag qid">'+escHtml(it["题型"])+'</span>';
    if(it["错因"]) meta+='<span class="tag reason">'+escHtml(it["错因"])+'</span>';
    if((it["错误次数"]||0)>0) meta+='<span class="tag err">错'+(it["错误次数"]||0)+'次</span>';
    if(it["日期"]) meta+='<span class="tag qid">'+escHtml(it["日期"])+'</span>';
    if(nextRev(it)) meta+='<span class="tag qid">下次 '+escHtml(nextRev(it))+'</span>';
    var optsHtml="";
    if(it["选项"] && it["选项"].length){
      // 错题本选项自带字母前缀（A. xxx / B. xxx），不再重复加
      optsHtml='<ul class="opts">'+it["选项"].map(function(o,i){return '<li data-i="'+i+'"><span class="opt-letter">'+String.fromCharCode(65+i)+'</span>'+renderMath(String(o).replace(/^[A-Z][\.、]\s*/, ''))+'</li>';}).join("")+'</ul>';
    }
    var ansHtml='<div class="feedback" id="fb"></div>'
      +'<div class="answer" id="ans">'
      +'<div><span class="k">答案：</span>'+renderMath(it["答案"]||"-")+'</div>'
      +(it["解析"]?'<div style="margin-top:6px"><span class="k">解析：</span>'+renderMath(it["解析"])+'</div>':'')
      +(it["知识点"]?'<div style="margin-top:6px"><span class="k">知识点：</span>'+renderMath(it["知识点"])+'</div>':'')
      +'</div>';
    var reasonHtml='<div class="reason-tools"><span>这次为什么错？</span>'
      +'<select id="reasonPick"><option value="">选择错因</option><option>概念不清</option><option>公式记错</option><option>方法不会</option><option>计算失误</option><option>审题失误</option><option>词汇不懂</option><option>语法不清</option><option>理解偏差</option><option>粗心</option><option>其他</option></select>'
      +'<button id="reasonSave">记录错因</button></div>';
    var similarHtml='<div class="similar"><div>再来一道同章节题</div>'
      +((it["同类题"]||[]).length?(it["同类题"]||[]).map(function(candidate,n){return '<a href="#" data-similar="'+n+'">'+renderMath(candidate.id+' · '+(candidate["题目"]||"未命名"))+'</a>';}).join(""):'<span>当前题库暂无可推荐的同章节题。</span>')
      +'</div>';
    box.innerHTML=
      '<div class="card">'
      +'<div class="meta">'+meta+(String(it.id||"").indexOf("L-")===0?'<span style="margin-left:auto;display:flex;gap:6px;"><button id="btnDelAll" style="background:#999;color:#fff;border:none;border-radius:6px;padding:2px 10px;font-size:12px;cursor:pointer;">删除所有</button><button id="btnDel" style="background:#EA6668;color:#fff;border:none;border-radius:6px;padding:2px 10px;font-size:12px;cursor:pointer;">删除此题</button></span>':'')+'</div>'
      +'<div class="qtext">'+renderMath(it["题目"])+'</div>'
      +optsHtml
      +'<div class="btns">'
      +(revealed?'':'<button id="btnShow">显示答案</button>')
      +'<button id="btnAgain" class="u">没记住 · 明天</button>'
      +'<button id="btnHard" class="h">有点模糊 · 3 天后</button>'
      +'<button id="btnGood" class="m">掌握 · 延后复习</button>'
      +'<button id="btnAITeach">AI 讲题</button>'
      +'</div>'
      +ansHtml
      +reasonHtml
      +similarHtml
      +'<div class="nav"><button id="btnPrev">‹ 上一题</button><span style="font-size:12px;color:var(--sub);align-self:center;">'+(idx+1)+' / '+list.length+'</span><button id="btnNext">下一题 ›</button></div>'
      +'</div>';
    var a=$("ans"); if(a) a.style.display = revealed?"block":"none";
    var fb=$("fb");
    function fbShow(msg,cls){ if(fb){ fb.innerHTML=msg; fb.className="feedback "+cls; fb.style.display="block"; } }
    function revealAnswer(){ revealed=true; answered=true; var aa=$("ans"); if(aa) aa.style.display="block"; var bs=$("btnShow"); if(bs) bs.style.display="none"; }
    function answerIndex(q){
      var ans=String(q["答案"]||"").trim();
      if(/^[A-H]$/.test(ans)) return ans.charCodeAt(0)-65;
      if(q["选项"]&&q["选项"].length){
        var i=q["选项"].indexOf(ans);
        if(i>=0) return i;
        // 判断题：答案为"对/错"等文字时，映射到含对应文字的选项
        var isJudge=String(q["题型"]||"").indexOf("判断")>=0;
        if(isJudge){
          if(/^(对|正确|是|T|True|√|真)$/i.test(ans)){ for(var j=0;j<q["选项"].length;j++) if(/对|正确|是|√|真/.test(q["选项"][j])) return j; }
          if(/^(错|错误|否|F|False|×|假)$/i.test(ans)){ for(var j=0;j<q["选项"].length;j++) if(/错|错误|否|×|假/.test(q["选项"][j])) return j; }
        }
        // 通用子串匹配（答案是选项文本的一部分）
        for(var j=0;j<q["选项"].length;j++) if(q["选项"][j].indexOf(ans)>=0) return j;
      }
      return -1;
    }
    var optsEls=box.querySelectorAll(".opts li");
    if(optsEls.length){
      var multi=String(it["题型"]||"").indexOf("多选")>=0;
      if(multi){
        optsEls.forEach(function(li){ li.addEventListener("click",function(){ if(answered||revealed) return; li.classList.toggle("sel"); }); });
        var subBtn=document.createElement("button");
        subBtn.id="btnSubmit"; subBtn.textContent="提交答案"; subBtn.className="m";
        var btnsBox=box.querySelector(".btns");
        if(btnsBox) btnsBox.insertBefore(subBtn, btnsBox.firstChild);
        subBtn.addEventListener("click",function(){
          if(answered||revealed) return;
          var selSet=[]; optsEls.forEach(function(o,i){ if(o.classList.contains("sel")) selSet.push(i); });
          var ans=String(it["答案"]||"").trim(), okSet=[];
          for(var k=0;k<ans.length;k++){ var c=ans.charCodeAt(k)-65; if(c>=0&&c<optsEls.length) okSet.push(c); }
          var correct=selSet.length===okSet.length && okSet.every(function(x){return selSet.indexOf(x)>=0;});
          optsEls.forEach(function(o){
            o.classList.remove("sel");
            var idx=parseInt(o.getAttribute("data-i"),10);
            if(okSet.indexOf(idx)>=0) o.classList.add("right");
            else if(selSet.indexOf(idx)>=0) o.classList.add("wrong");
          });
          if(correct){ fbShow("✔ 答对了！","ok"); }
          else{ fbShow("✘ 答错了，正确答案是 "+String(it["答案"])+"。","no"); }
          revealAnswer();
        });
      }else{
        optsEls.forEach(function(li){
          li.addEventListener("click",function(){
            if(answered||revealed) return;
            var ai=answerIndex(it), sel=parseInt(li.getAttribute("data-i"),10);
            if(sel===ai){ li.classList.add("right"); fbShow("✔ 答对了！","ok"); }
            else{
              li.classList.add("wrong");
              optsEls.forEach(function(o){ if(parseInt(o.getAttribute("data-i"),10)===ai) o.classList.add("right"); });
              fbShow("✘ 答错了，正确答案是 "+String(it["答案"])+"。","no");
            }
            revealAnswer();
          });
        });
      }
    }
    var reasonPick=$("reasonPick");
    if(reasonPick) reasonPick.value=it["错因"]||"";
    box.querySelectorAll("a[data-similar]").forEach(function(link){
      link.onclick=function(event){
        event.preventDefault();
        var candidate=(it["同类题"]||[])[Number(link.getAttribute("data-similar"))];
        if(!candidate) return;
        // 同类题来自题库，可能不在ALL里，直接加入list最前面
        list=[candidate].concat(list.filter(function(x){return x!==candidate;}));
        idx=0; revealed=false; show();
      };
    });
    bind();
  }
  function bind(){
    var s=$("btnShow"); if(s) s.onclick=function(){ revealed=true; show(); };
    var ai=$("btnAITeach"); if(ai) ai.onclick=function(){
      var q=list[idx];
      if(!q){ return; }
      var p="请帮我讲解这道专升本错题，讲清楚考点和解题思路：\n\n";
      p+="【题型】"+(q["题型"]||"")+"\n";
      p+="【题目】"+(q["题目"]||"")+"\n";
      if(q["选项"]&&q["选项"].length){
        var L="ABCDEFGH";
        p+="【选项】\n"+q["选项"].map(function(o,i){ return L[i]+". "+o; }).join("\n");
      }
      p+="\n【答案】"+(q["答案"]||"")+"\n";
      if(q["解析"]&&q["解析"]!=="（本题未附解析）") p+="【解析】"+q["解析"]+"\n";
      p+="\n请分点讲解：1) 考点是什么；2) 为什么选这个答案；3) 其他选项错在哪。";
      if(window.AIAsk){ window.AIAsk(p, "AI讲题 · Q-"+q.id); }
    };
    var a=$("btnAgain"); if(a) a.onclick=function(){ schedule(list[idx],"again"); revealed=false; if(idx<list.length-1){idx++;} show(); renderStats(); };
    var h=$("btnHard"); if(h) h.onclick=function(){ schedule(list[idx],"hard"); revealed=false; if(idx<list.length-1){idx++;} show(); renderStats(); };
    var g=$("btnGood"); if(g) g.onclick=function(){ schedule(list[idx],"good"); revealed=false; if(idx<list.length-1){idx++;} show(); renderStats(); };
    var rs=$("reasonSave"); if(rs) rs.onclick=function(){ var reason=$("reasonPick").value; if(!reason){return;} recordReason(list[idx],reason,false); save(); renderFactor(); renderWeak(); show(); };
    var p=$("btnPrev"); if(p) p.onclick=function(){ if(idx>0){idx--;revealed=false;show();} };
    var n=$("btnNext"); if(n) n.onclick=function(){ if(idx<list.length-1){idx++;revealed=false;show();} };
    var del=$("btnDel"); if(del) del.onclick=function(){
      if(!confirm("确定删除这道错题？删除后需重新做题存入。")) return;
      try{
        var cur=list[idx];
        var lkey="__SUBJECT___errorbook_local";
        var arr=JSON.parse(localStorage.getItem(lkey)||"[]");
        arr=arr.filter(function(x){ return x.id!==cur.id; });
        localStorage.setItem(lkey,JSON.stringify(arr));
      }catch(e){}
      location.reload();
    };
    var delAll=$("btnDelAll"); if(delAll) delAll.onclick=function(){
      if(!confirm("确定删除所有本地错题？此操作不可恢复！")) return;
      try{
        var lkey="__SUBJECT___errorbook_local";
        localStorage.removeItem(lkey);
      }catch(e){}
      location.reload();
    };
  }
  function reload(){ list=filtered(); idx=0; revealed=false; show(); renderStats(); }
  function setMode(btn){
    ["btnShuffle","btnOrder","btnKey","btnDue"].forEach(function(id){ $(id).classList.remove("on"); });
    $(btn).classList.add("on");
  }
  $("selChapter").onchange=function(){ setMode("btnOrder"); reload(); };
  $("selStatus").onchange=function(){ setMode("btnOrder"); reload(); };
  $("selReason").onchange=function(){ setMode("btnOrder"); reload(); };
  $("btnOrder").onclick=function(){ setMode("btnOrder"); reload(); };
  $("btnShuffle").onclick=function(){ setMode("btnShuffle"); list=filtered();
    for(var i=list.length-1;i>0;i--){ var j=Math.floor(Math.random()*(i+1)); var t=list[i]; list[i]=list[j]; list[j]=t; }
    idx=0; revealed=false; show(); renderStats(); };
  $("btnKey").onclick=function(){ setMode("btnKey"); list=filtered().filter(function(it){return (it["错误次数"]||0)>=2;}); idx=0; revealed=false; show(); renderStats(); };
  $("btnDue").onclick=function(){ setMode("btnDue"); list=filtered().filter(isDue); idx=0; revealed=false; show(); renderStats(); };
  $("btnReset").onclick=function(){
    if(this._arm){
      statusMap={}; revMap={}; planMap={}; save();
      this._arm=false; this.textContent="重置进度";
      this.style.background=""; this.style.color="";
      setTimeout(function(){ location.reload(); }, 300);
    }else{
      this._arm=true; this.textContent="再点一次确认重置";
      this.style.background="#EA6668"; this.style.color="#fff";
      var self=this;
      setTimeout(function(){ self._arm=false; self.textContent="重置进度"; self.style.background=""; self.style.color=""; }, 3000);
    }
  };
  $("btnExportLocal").onclick=function(){
    try{
      var _lkey="__SUBJECT___errorbook_local";
      var _local=JSON.parse(localStorage.getItem(_lkey)||"[]");
      if(!_local.length){ alert("本地暂无错题。在题库页做题并点「存入错题本」后，错题会自动存在这里。"); return; }
      var out="## 本地错题（手机端）\n\n";
      _local.forEach(function(it,i){
        out+="**练习 "+(i+1)+".** "+(it.题目||"")+"\n";
        if(it.选项&&it.选项.length){
          out+="- "+it.选项.map(function(o,j){return String.fromCharCode(65+j)+". "+o;}).join("　")+"\n";
        }
        out+="- **答案："+(it.答案||"")+"**　解析："+(it.解析||"")+"\n";
        out+="- 来源："+(it.来源||"")+"（"+(it.日期||"")+"）\n\n";
      });
      var ta=document.createElement("textarea");
      ta.value=out; document.body.appendChild(ta); ta.select();
      document.execCommand("copy"); ta.remove();
      alert("已复制 "+_local.length+" 道本地错题到剪贴板。\n粘贴到电脑端《错题本.md》末尾后运行 build.py 即可同步。");
    }catch(e){ alert("导出失败："+e.message); }
  };
  renderFactor();
  renderWeak();
  if(new URLSearchParams(location.search).get("mode")==="due") $("btnDue").click(); else reload();
})();
</script>
</body>
</html>
"""

# ============================================================
# 英语单词卡模板
# ============================================================
WORD_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>英语单词卡</title>
<style>
:root{--accent:#C9A7E8;--accent-d:#6D4BA3;--text:#1A1B1C;--sub:#6B7280;--bg:#F4F3EE;--card:#FFFFFF;--border:#E4E3DD;}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent;}
body{font-family:'Roboto','PingFang SC','Segoe UI',Arial,sans-serif;background:var(--bg);color:var(--text);padding:16px;line-height:1.6;}
.wrap{max-width:640px;margin:0 auto;}
h1{font-size:20px;font-weight:700;margin-bottom:2px;}
.back{font-size:12px;color:var(--sub);text-decoration:none;display:inline-block;margin-bottom:6px;}
.sub{font-size:12px;color:var(--sub);margin-bottom:12px;}
.stats{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;}
.stat{flex:1 1 90px;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:9px 12px;}
.stat .n{font-size:18px;font-weight:700;}
.stat .l{font-size:11px;color:var(--sub);}
.toolbar{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px;}
.toolbar input,.toolbar select,.toolbar button{font-size:13px;padding:7px 10px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--text);}
.toolbar button{cursor:pointer;}
.toolbar button.primary{background:var(--accent-d);color:#fff;border-color:var(--accent-d);font-weight:600;}
.card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:22px 18px;text-align:center;margin-bottom:12px;min-height:180px;display:flex;flex-direction:column;justify-content:center;align-items:center;}
.word{font-size:26px;font-weight:700;letter-spacing:.5px;}
.phon{font-size:13px;color:var(--sub);margin-top:6px;}
.detail{display:none;margin-top:14px;font-size:14px;line-height:1.8;}
.detail .pos{color:var(--accent-d);font-weight:600;}
.detail .ex{color:var(--sub);font-style:italic;font-size:13px;margin-top:4px;}
.detail .root{font-size:12px;color:var(--sub);margin-top:6px;}
.nav{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin-top:10px;}
.nav button{font-size:13px;padding:8px 14px;border:1px solid var(--border);border-radius:8px;background:var(--card);cursor:pointer;}
.nav button.k{background:rgba(82,196,26,0.14);border-color:#52C41A;color:#3E8C13;}
.nav button.f{background:rgba(250,173,20,0.18);border-color:#FAAD14;color:#8A5B00;}
.nav button.n{background:rgba(234,102,104,0.12);border-color:#EA6668;color:#B44244;}
.posinfo{font-size:12px;color:var(--sub);text-align:center;margin-top:10px;}
.hint{font-size:11.5px;color:var(--sub);margin-top:14px;line-height:1.7;}
.empty{text-align:center;color:var(--sub);font-size:13px;padding:30px 10px;background:var(--card);border:1px dashed var(--border);border-radius:14px;}
</style>
</head>
<body>
<div class="wrap">
  <a class="back" href="__INDEX__">‹ 返回错题本总入口</a>
  <h1>英语 · 单词卡</h1>
  <div class="sub">数据源：同目录《单词卡.md》 · 由 SCGSstudy/build.py 生成 · 翻卡记忆</div>

  <div class="stats">
    <div class="stat"><div class="n" id="nTotal">0</div><div class="l">总词数</div></div>
    <div class="stat"><div class="n" id="nKnow">0</div><div class="l">已掌握</div></div>
    <div class="stat"><div class="n" id="nFuzzy">0</div><div class="l">模糊</div></div>
    <div class="stat"><div class="n" id="nNo">0</div><div class="l">未记住</div></div>
  </div>

  <div class="toolbar">
    <input id="inpSearch" placeholder="搜索单词/释义…" style="flex:1 1 140px;min-width:0;">
    <button id="btnShuffle" class="primary">随机抽词</button>
    <button id="btnOrder">顺序浏览</button>
    <button id="btnFuzzy">只背模糊词</button>
    <button id="btnReset">重置</button>
  </div>

  <div class="card" id="card"></div>
  <div class="nav">
    <button id="btnFlip">翻看释义</button>
    <button id="btnK" class="k">认识</button>
    <button id="btnF" class="f">模糊</button>
    <button id="btnN" class="n">不认识</button>
  </div>
  <div class="posinfo" id="pos">— / —</div>

  <div class="hint">
    看到单词 → 心里默念释义 → 点「翻看释义」核对 → 按掌握程度点「认识 / 模糊 / 不认识」（状态自动保存）。<br>
    更新：往《单词卡.md》按格式追加生词，运行 SCGSstudy/build.py 重新生成。
  </div>
</div>

<script>
window.__WORDS__ = __WORDS_JSON__;
try{var _sync=JSON.parse(localStorage.getItem("errorbook_sync")||"null");if(_sync&&_sync["英语"]&&_sync["英语"].words){window.__WORDS__=_sync["英语"].words;}}catch(e){}
(function(){
  "use strict";
  var ALL=(window.__WORDS__||[]).slice();
  var key="yingyu_wordcard_v1";
  var stMap={};
  try{ stMap=JSON.parse(localStorage.getItem(key)||"{}")||{}; }catch(e){ stMap={}; }
  function save(){ try{ localStorage.setItem(key,JSON.stringify(stMap)); }catch(e){} }
  function st(it){ return stMap[it.id]||it["状态"]||"待复习"; }
  function setSt(id,v){ stMap[id]=v; save(); }

  var list=[], idx=0, flipped=false;
  function $(id){ return document.getElementById(id); }
  function esc(s){ return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }

  function pool(){
    var q=($("inpSearch").value||"").trim().toLowerCase();
    var onlyFuzzy=$("btnFuzzy").classList.contains("on");
    return ALL.filter(function(it){
      if(onlyFuzzy && st(it)!=="模糊") return false;
      if(!q) return true;
      var hay=(it["单词"]+" "+(it["释义"]||"")+" "+(it["词性"]||"")).toLowerCase();
      return hay.indexOf(q)>=0;
    });
  }
  function stats(){
    var k=0,f=0,n=0;
    ALL.forEach(function(it){ var s=st(it); if(s==="已掌握")k++; else if(s==="模糊")f++; else n++; });
    $("nTotal").textContent=ALL.length; $("nKnow").textContent=k; $("nFuzzy").textContent=f; $("nNo").textContent=n;
  }
  function show(){
    var box=$("card");
    if(!list.length){
      box.innerHTML='<div class="empty">当前范围没有单词。<br>往《单词卡.md》追加生词并运行 build.py 重新生成。</div>';
      $("btnFlip").style.visibility="hidden"; $("btnK").style.visibility="hidden"; $("btnF").style.visibility="hidden"; $("btnN").style.visibility="hidden";
      $("pos").textContent="0 / 0"; return;
    }
    $("btnFlip").style.visibility="visible"; $("btnK").style.visibility="visible"; $("btnF").style.visibility="visible"; $("btnN").style.visibility="visible";
    var it=list[idx];
    var html='<div class="word">'+esc(it["单词"])+'</div>';
    if(it["音标"]) html+='<div class="phon">'+esc(it["音标"])+'</div>';
    html+='<div class="detail" id="detail">';
    if(it["词性"]) html+='<div><span class="pos">'+esc(it["词性"])+'</span> '+esc(it["释义"]||"")+'</div>';
    else if(it["释义"]) html+='<div>'+esc(it["释义"])+'</div>';
    if(it["例句"]) html+='<div class="ex">'+esc(it["例句"])+'</div>';
    if(it["词根"]) html+='<div class="root">词根：'+esc(it["词根"])+'</div>';
    html+='</div>';
    box.innerHTML=html;
    $("detail").style.display = flipped?"block":"none";
    $("pos").textContent=(idx+1)+" / "+list.length;
  }
  function reload(){ list=pool(); idx=0; flipped=false; show(); stats(); }
  $("btnFlip").onclick=function(){ flipped=true; var d=$("detail"); if(d) d.style.display="block"; };
  $("btnK").onclick=function(){ if(!list.length)return; setSt(list[idx].id,"已掌握"); flipped=false; if(idx<list.length-1)idx++; show(); stats(); };
  $("btnF").onclick=function(){ if(!list.length)return; setSt(list[idx].id,"模糊"); flipped=false; if(idx<list.length-1)idx++; show(); stats(); };
  $("btnN").onclick=function(){ if(!list.length)return; setSt(list[idx].id,"不认识"); flipped=false; if(idx<list.length-1)idx++; show(); stats(); };
  $("inpSearch").oninput=function(){ reload(); };
  $("btnShuffle").onclick=function(){ list=pool();
    for(var i=list.length-1;i>0;i--){ var j=Math.floor(Math.random()*(i+1)); var t=list[i]; list[i]=list[j]; list[j]=t; }
    idx=0; flipped=false; show(); };
  $("btnOrder").onclick=function(){ $("btnFuzzy").classList.remove("on"); reload(); };
  $("btnFuzzy").onclick=function(){ $("btnFuzzy").classList.toggle("on"); reload(); };
  $("btnReset").onclick=function(){
    if(this._arm){
      stMap={}; save();
      this._arm=false; this.textContent="重置";
      this.style.background=""; this.style.color="";
      setTimeout(function(){ location.reload(); }, 300);
    }else{
      this._arm=true; this.textContent="再点一次确认重置";
      this.style.background="#EA6668"; this.style.color="#fff";
      var self=this;
      setTimeout(function(){ self._arm=false; self.textContent="重置"; self.style.background=""; self.style.color=""; }, 3000);
    }
  };
  reload();
})();
</script>
</body>
</html>
"""


def select_key_questions(subject, tiku_items):
    """重点题 = 真题高频考点的练习题。
    真题题按内容归类算考点 → 考点在真题中出现 ≥2 次为高频 → 该考点下的练习题（非真题）为重点题。
    数量上限 180 题，超出时按高频考点优先级截断。
    排除兜底专题"综合"（内容关键词推断失败的归属，不是真实考点）。
    """
    freq = Counter()
    for it in tiku_items:
        if it["id"].startswith("真题-"):
            tp = topic_from_content(subject, it)
            if tp == "综合":
                continue
            freq[tp] += 1
    hot = [tp for tp, n in freq.items() if n >= 2]
    hot.sort(key=lambda tp: -freq[tp])
    keys = [it for it in tiku_items
            if not it["id"].startswith("真题-") and it.get("专题") in hot]
    # 每高频考点取前 15 道练习题（md 顺序），保证各考点均匀覆盖
    out = []
    for tp in hot:
        out.extend([x for x in keys if x["专题"] == tp][:15])
    return out


def build_review(sub):
    """生成单科复习页。"""
    name = sub["name"]
    d = sub["dir"]
    md = d / "错题本.md"
    items = parse_md(md)
    tiku_items = parse_tiku(d.parent / "题库.md", name)
    for item in items:
        same_type = [candidate for candidate in tiku_items
                     if candidate.get("章节") == item.get("章节")
                     and candidate.get("题型") == item.get("题型")
                     and candidate.get("题目") != item.get("题目")]
        same_chapter = [candidate for candidate in tiku_items
                        if candidate.get("章节") == item.get("章节")
                        and candidate.get("题目") != item.get("题目")]
        matches = (same_type + [candidate for candidate in same_chapter if candidate not in same_type])[:3]
        item["同类题"] = matches
    mode = sub["mode"]
    katex_css = ""
    katex_js = ""
    if mode == "math":
        katex_css = '<link rel="stylesheet" href="../../SCGSstudy/katex/katex.min.css">'
        katex_js = "../../SCGSstudy/katex/katex.min.js"
    # 题库精简数据（仅id+题目+选项），用于补全本地错题缺失的选项
    tiku_simple = [{"id": t["id"], "题目": t["题目"], "选项": t["选项"]} for t in tiku_items]
    html = (REVIEW_HTML
            .replace("__LABEL__", sub["label"])
            .replace("__COLOR__", sub["color"])
            .replace("__MODE__", mode)
            .replace("__DATA_JSON__", js_safe(items))
            .replace("__TIKU_SIMPLE_JSON__", js_safe(tiku_simple))
            .replace("__SUBJECT___cuowuji", name + "_cuowuji")
            .replace("__SUBJECT__", name)
            .replace("__KATEX_CSS__", katex_css)
            .replace("__KATEX_JS__", katex_js)
            .replace("__INDEX__", "../../SCGSstudy/index.html"))
    html = html.replace("var MATH = __MATH_MODE__;",
                        "var MATH = %s;" % ("true" if mode == "math" else "false"))
    html = html.replace("</body>", AI_HTML + SUBMIT_HTML + "\n</body>")
    out = d / "复习页.html"
    out.write_text(html, encoding="utf-8")
    return items


def build_wordcard(sub):
    """生成英语单词卡页。"""
    d = sub["dir"]
    md = d / "单词卡.md"
    items = parse_md(md, prefix="W")
    html = (WORD_HTML
            .replace("__WORDS_JSON__", js_safe(items))
            .replace("__INDEX__", "../../SCGSstudy/index.html"))
    html = html.replace("</body>", AI_HTML + SUBMIT_HTML + "\n</body>")
    out = d / "单词卡.html"
    out.write_text(html, encoding="utf-8")
    return items


def parse_wordbook(path):
    """解析《单词本.md》：每行一个词条 `- word [音标] pos. 释义 【来源】`。"""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    words = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("---") or line.startswith("#"):
            continue
        m = re.match(r"^-\s*(.+)$", line)
        if not m:
            continue
        rest = m.group(1).strip()
        wm = re.match(r"^(\S+)(?:\s+\[([^\]]*)\])?(?:\s+([a-z]{1,4})\.)?\s*(.*)$", rest)
        if not wm or not wm.group(1):
            continue
        word = wm.group(1)
        phon = (wm.group(2) or "").strip()
        pos = (wm.group(3) or "").strip()
        mean = (wm.group(4) or "").strip()
        # 提取来源标记 【通用】【四级】【专升本】
        tag = ""
        mt = re.search(r"【([^】]*)】\s*$", mean)
        if mt:
            tag = mt.group(1)
            mean = mean[: mt.start()].strip()
        words.append([word, phon, pos, mean, tag])
    return words


def build_wordbook(sub):
    """生成《单词本.html》：完整词库 浏览/搜索/翻卡/标记生词。"""
    d = sub["dir"]
    md = d / "单词本.md"
    words = parse_wordbook(md)
    tpl = (BASE / "wordbook_tpl.html").read_text(encoding="utf-8")
    html = (tpl
            .replace("__WORDS_JSON__", js_safe(words))
            .replace("__INDEX__", "../../SCGSstudy/index.html"))
    html = html.replace("</body>", AI_HTML + SUBMIT_HTML + "\n</body>")
    out = d / "单词本.html"
    out.write_text(html, encoding="utf-8")
    return words


def build_shengci(sub):
    """生成《生词本.html》：网页标星生词 + 手动写入生词本.md 的词。"""
    d = sub["dir"]
    words = parse_wordbook(d / "单词本.md")
    manual = parse_md(d / "生词本.md", prefix="W")
    tpl = (BASE / "shengci_tpl.html").read_text(encoding="utf-8")
    html = (tpl
            .replace("__WORDS_JSON__", js_safe(words))
            .replace("__MANUAL_JSON__", js_safe(manual))
            .replace("__INDEX__", "../../SCGSstudy/index.html"))
    html = html.replace("</body>", AI_HTML + SUBMIT_HTML + "\n</body>")
    out = d / "生词本.html"
    out.write_text(html, encoding="utf-8")
    return len(manual)


# ============================================================
# 题库刷题页模板（刷题 → 错题一键导出入库）
# ============================================================
TIKU_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__LABEL__ · 题库刷题</title>
<style>
:root{--accent:__COLOR__;--accent-d:#33475C;--text:#1A1B1C;--sub:#6B7280;--bg:#F4F3EE;--card:#FFFFFF;--border:#E4E3DD;}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent;}
body{font-family:'Roboto','PingFang SC','Segoe UI',Arial,sans-serif;background:var(--bg);color:var(--text);padding:16px;line-height:1.6;}
.wrap{max-width:760px;margin:0 auto;}
h1{font-size:20px;font-weight:700;margin-bottom:2px;}
.back{font-size:12px;color:var(--sub);text-decoration:none;display:inline-block;margin-bottom:6px;}
.sub{font-size:12px;color:var(--sub);margin-bottom:12px;}
.stats{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;}
.stat{flex:1 1 110px;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:9px 12px;}
.stat .n{font-size:18px;font-weight:700;}
.stat .l{font-size:11px;color:var(--sub);}
.stat.hot{border-color:var(--accent);}
.toolbar{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px;}
.toolbar select,.toolbar button{font-size:13px;padding:7px 10px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--text);cursor:pointer;}
.toolbar button.primary{background:var(--accent-d);color:#fff;border-color:var(--accent-d);font-weight:600;}
.toolbar button.on{background:var(--accent);border-color:var(--accent);color:#1A1B1C;font-weight:600;}
.toolbar button.danger{background:rgba(234,102,104,0.14);border-color:#EA6668;color:#B44244;font-weight:600;}
.card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:16px;margin-bottom:12px;}
.meta{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-bottom:10px;}
.tag{font-size:11px;padding:2px 8px;border-radius:10px;background:var(--accent);color:#22304A;}
.tag.qid{background:rgba(0,0,0,0.06);color:var(--sub);}
.tag.src{background:rgba(0,0,0,0.05);color:var(--sub);}
.material{background:rgba(0,0,0,0.035);border-left:3px solid var(--accent);padding:10px 12px;border-radius:0 8px 8px 0;margin-bottom:10px;font-size:13px;white-space:pre-wrap;}
.word-clickable{cursor:pointer;border-bottom:1px dashed #9BBBF4;color:#2B5A9E;padding:0 1px;border-radius:2px;transition:background .15s;}
.word-clickable:hover{background:rgba(155,187,244,0.18);}
.word-clickable.word-saved{background:rgba(234,167,178,0.18);border-bottom-color:#EAA7B2;color:#B44244;}
.qtext{font-size:15px;font-weight:600;margin-bottom:10px;white-space:pre-wrap;}
.opts{list-style:none;margin-bottom:10px;}
.opts li{font-size:13.5px;padding:10px 14px;border:1.5px solid var(--border);border-radius:10px;margin-bottom:8px;background:#FBFBF8;cursor:pointer;transition:all .18s ease;position:relative;user-select:none;-webkit-tap-highlight-color:transparent;}
.opts li:active{transform:scale(0.97);}
.opts li:hover{border-color:var(--accent);background:rgba(155,187,244,0.06);}
.opts li.sel{border-color:var(--accent-d);background:rgba(0,0,0,0.04);}
.opts li.right{border-color:#52C41A;background:rgba(82,196,26,0.12);animation:pulse .5s ease;}
.opts li.wrong{border-color:#EA6668;background:rgba(234,102,104,0.10);animation:shake .4s ease;}
.opts li .opt-letter{display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:6px;background:rgba(0,0,0,0.06);font-weight:700;font-size:12px;margin-right:8px;flex:0 0 auto;}
.opts li.sel .opt-letter{background:var(--accent-d);color:#fff;}
.opts li.right .opt-letter{background:#52C41A;color:#fff;}
.opts li.wrong .opt-letter{background:#EA6668;color:#fff;}
@keyframes shake{0%,100%{transform:translateX(0);}20%{transform:translateX(-6px);}40%{transform:translateX(6px);}60%{transform:translateX(-4px);}80%{transform:translateX(4px);}}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(82,196,26,0.4);}70%{box-shadow:0 0 0 10px rgba(82,196,26,0);}100%{box-shadow:0 0 0 0 rgba(82,196,26,0);}}
.answer{display:none;border-left:3px solid var(--accent-d);background:rgba(155,187,244,0.10);padding:10px 12px;border-radius:0 8px 8px 0;margin-bottom:10px;font-size:13.5px;white-space:pre-wrap;}
.answer .k{font-weight:700;color:var(--accent-d);}
.feedback{display:none;font-size:13.5px;font-weight:600;margin-bottom:10px;padding:8px 12px;border-radius:8px;}
.feedback.ok{background:rgba(82,196,26,0.12);color:#3E8C13;}
.feedback.no{background:rgba(234,102,104,0.10);color:#B44244;}
.btns{display:flex;gap:8px;flex-wrap:wrap;}
.btns button{font-size:13px;padding:8px 14px;border:1px solid var(--border);border-radius:8px;background:#fff;color:var(--text);cursor:pointer;}
.btns button.g{background:rgba(82,196,26,0.14);border-color:#52C41A;color:#3E8C13;font-weight:600;}
.btns button.r{background:rgba(234,102,104,0.12);border-color:#EA6668;color:#B44244;font-weight:600;}
.btns button.d{background:rgba(250,173,20,0.16);border-color:#FAAD14;color:#8A5B00;font-weight:600;}
.nav{display:flex;justify-content:space-between;gap:8px;margin-top:12px;}
.nav button{font-size:13px;padding:8px 14px;border:1px solid var(--border);border-radius:8px;background:var(--card);cursor:pointer;}
.basket{background:var(--card);border:1px dashed var(--accent);border-radius:14px;padding:14px 16px;margin-bottom:12px;}
.basket .bt{font-size:13px;font-weight:700;margin-bottom:8px;}
.basket .blist{font-size:12.5px;color:var(--text);}
.basket .blist div{display:flex;gap:8px;align-items:flex-start;margin-bottom:4px;}
.basket .blist span{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.basket .blist button{font-size:11px;padding:2px 8px;border:1px solid var(--border);border-radius:6px;background:#fff;cursor:pointer;color:var(--sub);}
.basket .actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;}
.basket .actions button{font-size:13px;padding:7px 12px;border:1px solid var(--border);border-radius:8px;cursor:pointer;}
.basket .actions .exp{background:var(--accent-d);color:#fff;border-color:var(--accent-d);font-weight:600;}
.expout{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:14px 16px;margin-bottom:12px;}
.expout textarea{width:100%;min-height:150px;font-family:Consolas,monospace;font-size:12px;border:1px solid var(--border);border-radius:8px;padding:10px;background:#FBFBF8;color:var(--text);}
#toast{position:fixed;left:50%;bottom:28px;transform:translateX(-50%);background:#33475C;color:#fff;font-size:13px;padding:10px 18px;border-radius:10px;max-width:88vw;box-shadow:0 4px 16px rgba(0,0,0,0.18);z-index:99;display:none;line-height:1.5;}
.empty{text-align:center;color:var(--sub);font-size:13px;padding:30px 10px;background:var(--card);border:1px dashed var(--border);border-radius:14px;}
.hint{font-size:11.5px;color:var(--sub);margin-top:12px;line-height:1.7;}
.math-inline{display:inline-block;vertical-align:middle;}
/* 移动端适配 */
@media (max-width:480px){
  .toolbar select,.toolbar button{min-height:44px;font-size:14px;}
  .opts li{min-height:44px;display:flex;align-items:center;font-size:14px;padding:10px 12px;}
  .btns button{min-height:44px;font-size:14px;}
  .nav button{min-height:44px;font-size:14px;}
  .basket .actions button{min-height:44px;}
  .qtext{font-size:16px;}
}
</style>
__KATEX_CSS__
</head>
<body>
<div class="wrap">
  <a class="back" href="__INDEX__">‹ 返回错题本总入口</a>
  <h1>__LABEL__ · 题库刷题</h1>  <div class="sub">数据源：同目录《题库.md》 · 做错一键入篮，一键存入《错题本.md》</div>

  <div class="stats">
    <div class="stat"><div class="n" id="nTotal">0</div><div class="l">题库总题</div></div>
    <div class="stat"><div class="n" id="nDone">0</div><div class="l">已完成</div></div>
    <div class="stat"><div class="n" id="nLeft">0</div><div class="l">本组待做</div></div>
    <div class="stat hot"><div class="n" id="nBasket">0</div><div class="l">错题篮子</div></div>
  </div>

  <div class="toolbar">
    <select id="selTopic"><option value="">全部专题</option></select>
    <select id="selKaodian" style="display:none;"><option value="">全部考点</option></select>
    <button id="btnShuffle" class="primary">随机抽题</button>
    <button id="btnOrder">顺序浏览</button>
    <button id="btnKey">重点题</button>
    <button id="btnUndone">只看未做</button>
    <button id="btnBasket">错题篮子</button>
    <button id="btnReset">重置进度</button>
    <button id="btnClozeMode" style="display:none;background:#EAA7B2;color:#fff;">完形全文：关</button>
  </div>

  <div id="card"></div>

  <div class="basket" id="basketBox">
    <div class="bt">错题篮子（做错的题会进这里，可一键存入错题本）</div>
    <div class="blist" id="basketList"></div>
    <div class="actions">
      <button class="exp" id="btnExport">存入错题本</button>
      <button id="btnClearBasket">清空篮子</button>
    </div>
  </div>

  <div class="expout" id="expBox" style="display:none;">
    <div class="sub" style="margin-bottom:6px;">当前页面不是从“启动错题本”打开，无法直接写入文件。请复制以下内容，粘贴到本学科《错题集\SCGSstudy.md》末尾：</div>
    <textarea id="expText" readonly></textarea>
  </div>

  <div id="toast"></div>
  <div id="passageModal" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:9999;justify-content:center;align-items:center;padding:20px;">
    <div style="background:#fff;border-radius:16px;max-width:700px;width:100%;max-height:85vh;overflow-y:auto;padding:24px;position:relative;">
      <button id="passageClose" aria-label="关闭全文" style="position:absolute;top:12px;right:16px;font-size:22px;cursor:pointer;color:#999;line-height:1;background:none;border:none;padding:6px;">×</button>
      <h3 style="margin-bottom:14px;font-size:16px;">📖 完形填空 · 本篇全文</h3>
      <div id="passageContent" style="font-size:14px;line-height:1.8;color:#333;white-space:pre-wrap;"></div>
      <div style="margin-top:16px;font-size:12px;color:#999;">💡 点击文中蓝色单词可加入生词本</div>
    </div>
  </div>

  <div class="hint">
    操作：看题 → 点选答案判对错（或点「显示答案」）→ 按结果点「做对了」或「做错了·记入错题」→ 攒够一批点「存入错题本」。从“启动错题本”打开时，系统会自动写入并更新复习页。<br>
    章节、序号、选项格式已自动生成；直接双击 HTML 打开时仍可导出文本作为兼容方案。
  </div>
</div>

<script src="__KATEX_JS__"></script>
<script>
window.__TIKU__ = __TIKU_JSON__;
window.__KEY_ITEMS__ = __KEY_JSON__;
window.__TIKU_META__ = {baseQid: __BASE_QID_VAL__};
try{var _sync=JSON.parse(localStorage.getItem("errorbook_sync")||"null");if(_sync&&_sync["__SUBJECT__"]&&_sync["__SUBJECT__"].tiku){window.__TIKU__=_sync["__SUBJECT__"].tiku;}}catch(e){}
(function(){
  "use strict";
  var MATH = __MATH_MODE__;
  var SUBJECT = "__SUBJECT__";
  var IS_EN = SUBJECT === "英语";
  var ALL = (window.__TIKU__||[]).slice();
  var KEY_ITEMS=(window.__KEY_ITEMS__||[]).slice();
  var BASE_QID = parseInt((window.__TIKU_META__&&window.__TIKU_META__.baseQid)||1,10);
  var storeKey = "__SUBJECT___tiku_v1";
  var done={}, basket=[], nextId=BASE_QID;
  try{ var saved=JSON.parse(localStorage.getItem(storeKey)||"{}")||{}; done=saved.dn||{}; basket=saved.bk||[]; nextId=saved.nx||BASE_QID; }catch(e){}
  function save(){ try{ localStorage.setItem(storeKey, JSON.stringify({dn:done,bk:basket,nx:nextId})); }catch(e){} }

  function $(id){ return document.getElementById(id); }
  function escHtml(s){ return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
  function showToast(msg, ms){
    var el=document.getElementById("toast");
    if(!el) return;
    el.textContent=msg; el.style.display="block";
    clearTimeout(el._t);
    el._t=setTimeout(function(){ el.style.display="none"; }, ms||4200);
  }
  function copyText(txt){
    var done=false;
    try{
      if(navigator.clipboard&&navigator.clipboard.writeText){
        navigator.clipboard.writeText(txt).then(function(){done=true;}).catch(function(){});
      }
    }catch(e){}
    return done;
  }
  function renderMath(s){
    var t=escHtml(s);
    // 保护反引号代码块（如Excel公式 $A$1、Shell $var），避免被KaTeX当数学公式
    var codes=[];
    t=t.replace(/`([^`]*)`/g, function(_,c){ codes.push(c); return "\u0000CODE"+(codes.length-1)+"\u0000"; });
    // 保护 Excel 单元格绝对/混合引用（$A$1、$A1、A$1），避免被KaTeX当数学公式
    var xls=[];
    t=t.replace(/\$[A-Z]{1,3}\$[0-9]{1,7}|\$[A-Z]{1,3}[0-9]{1,7}|[A-Z]{1,3}\$[0-9]{1,7}/g, function(m){ xls.push(m); return "\u0000XLS"+(xls.length-1)+"\u0000"; });
    function restoreXls(t){
      return t.replace(/\u0000XLS(\d+)\u0000/g, function(_,i){ return xls[+i]||""; });
    }
    function restore(t){
      return t.replace(/\u0000CODE(\d+)\u0000/g, function(_,i){
        return '<code style="background:rgba(0,0,0,0.06);border-radius:4px;padding:1px 6px;font-family:Consolas,Monaco,monospace;font-size:0.9em;color:#B44244;white-space:pre-wrap;word-break:break-all;">'+(codes[+i]||"")+'</code>';
      });
    }
    if(!MATH || typeof katex==="undefined") return restoreXls(restore(t));
    function unesc(x){ return x.replace(/&lt;/g,"<").replace(/&gt;/g,">").replace(/&amp;/g,"&").replace(/&quot;/g,'"'); }
    try{
      t=t.replace(/\$\$([\s\S]+?)\$\$/g,function(_,x){ return '<div class="math-inline" style="margin:6px 0;">'+katex.renderToString(unesc(x),{displayMode:true,throwOnError:false})+'</div>'; });
      t=t.replace(/\$([^$\n]+?)\$/g,function(_,x){ return '<span class="math-inline">'+katex.renderToString(unesc(x),{displayMode:false,throwOnError:false})+'</span>'; });
    }catch(e){}
    return restoreXls(restore(t));
  }
  // 英语刷题：把文本中的英文单词标记为可点击，点击加入生词本
  var SHENGCI_KEY="yingyu_shengci_v1";
  function loadShengci(){ try{ return JSON.parse(localStorage.getItem(SHENGCI_KEY)||"{}")||{}; }catch(e){ return {}; } }
  function saveShengci(obj){ try{ localStorage.setItem(SHENGCI_KEY,JSON.stringify(obj)); }catch(e){} }
  function isShengci(word){ var sc=loadShengci(); return !!sc[word.toLowerCase()]; }
  function addShengci(word){
    var w=word.toLowerCase();
    var sc=loadShengci();
    if(sc[w]){ showToast("「"+word+"」已在生词本中"); return false; }
    sc[w]={t:new Date().toISOString().slice(0,10),s:""};
    saveShengci(sc);
    showToast("已加入生词本："+word);
    return true;
  }
  function markWords(text){
    if(!IS_EN) return renderMath(text);
    var t=escHtml(text);
    // 反引号代码块不标记生词
    var codes=[];
    t=t.replace(/`([^`]*)`/g, function(_,c){ codes.push(c); return "\u0000CODE"+(codes.length-1)+"\u0000"; });
    // 匹配2个字母以上的英文单词（含连字符、撇号），不匹配纯数字
    t=t.replace(/\b([a-zA-Z][a-zA-Z'-]{1,})\b/g, function(m,w){
      var cls="word-clickable"+(isShengci(w)?" word-saved":"");
      return '<span class="'+cls+'" data-word="'+w.toLowerCase()+'">'+m+'</span>';
    });
    t=t.replace(/\u0000CODE(\d+)\u0000/g, function(_,i){
      return '<code style="background:rgba(0,0,0,0.06);border-radius:4px;padding:1px 6px;font-family:Consolas,Monaco,monospace;font-size:0.9em;color:#B44244;white-space:pre-wrap;word-break:break-all;">'+(codes[+i]||"")+'</code>';
    });
    return t;
  }

  if(IS_EN){
    var hintEl=document.querySelector(".hint");
    if(hintEl) hintEl.innerHTML+='<br><span style="color:#2B5A9E;">💡 英语刷题：点击<b>题目/阅读材料</b>中的蓝色单词可加入生词本（粉色=已加入）；选项整体是答题按钮，点击选项直接作答。完形填空可点「查看本篇全文」看完整文章。</span>';
  }
  // 完形填空弹窗
  function openPassage(text){
    if(!text) return;
    var modal=$("passageModal"), content=$("passageContent");
    content.innerHTML=markWords(text);
    modal.style.display="flex";
    // 弹窗内单词点击加入生词本
    content.querySelectorAll(".word-clickable").forEach(function(el){
      el.addEventListener("click", function(e){
        e.stopPropagation();
        var w=el.getAttribute("data-word");
        if(w && addShengci(w)) el.classList.add("word-saved");
      });
    });
  }
  function closePassage(){ $("passageModal").style.display="none"; }
  var _pc=$("passageClose"); if(_pc) _pc.onclick=closePassage;
  var _pm=$("passageModal"); if(_pm) _pm.addEventListener("click", function(e){ if(e.target===_pm) closePassage(); });
  document.addEventListener("keydown", function(e){ if(e.key==="Escape" && $("passageModal") && $("passageModal").style.display==="flex") closePassage(); });
  var topics=[];
  ALL.forEach(function(it){ if(topics.indexOf(it["专题"])<0) topics.push(it["专题"]); });
  topics.sort();
  topics.forEach(function(t){ var o=document.createElement("option"); o.value=t; o.textContent=t; $("selTopic").appendChild(o); });

  // 考点筛选（仅高数）
  if(SUBJECT==="高数"){
    var selK=$("selKaodian");
    if(selK){
      selK.style.display="inline-block";
      var kaodians=[];
      ALL.forEach(function(it){ var kd=it["考点"]||"99-综合"; if(kaodians.indexOf(kd)<0) kaodians.push(kd); });
      kaodians.sort();
      kaodians.forEach(function(k){ var o=document.createElement("option"); o.value=k; o.textContent=k; selK.appendChild(o); });
    }
  }

  var mode="shuffle"; // shuffle|order|key|undone|basket
  var clozeFullMode=false;
  try{ clozeFullMode=localStorage.getItem("yingyu_cloze_full")==="1"; }catch(e){}
  if(IS_EN){
    var btnCM=$("btnClozeMode");
    if(btnCM){
      btnCM.style.display="inline-block";
      btnCM.textContent=clozeFullMode?"完形全文：开":"完形全文：关";
      btnCM.onclick=function(){
        clozeFullMode=!clozeFullMode;
        try{ localStorage.setItem("yingyu_cloze_full", clozeFullMode?"1":"0"); }catch(e){}
        btnCM.textContent=clozeFullMode?"完形全文：开":"完形全文：关";
        show();
      };
    }
  }
  var list=[], idx=0, revealed=false, answered=false;
  function setMode(m){
    mode=m;
    ["btnShuffle","btnOrder","btnKey","btnUndone","btnBasket"].forEach(function(id){
      $("btnShuffle").classList.remove("on");$("btnOrder").classList.remove("on");$("btnKey").classList.remove("on");$("btnUndone").classList.remove("on");$("btnBasket").classList.remove("on");
    });
    if(m==="shuffle")$("btnShuffle").classList.add("on");
    else if(m==="order")$("btnOrder").classList.add("on");
    else if(m==="key")$("btnKey").classList.add("on");
    else if(m==="undone")$("btnUndone").classList.add("on");
    else if(m==="basket")$("btnBasket").classList.add("on");
    reload();
  }
  function pool(){
    var t=$("selTopic").value;
    var kd=$("selKaodian")?$("selKaodian").value:"";
    var keySet={};
    if(mode==="key"){ KEY_ITEMS.forEach(function(k){ keySet[k.id]=1; }); }
    var base=ALL.filter(function(it){
      if(t && it["专题"]!==t) return false;
      if(kd && (it["考点"]||"99-综合")!==kd) return false;
      if(mode==="basket") return basket.indexOf(it.id)>=0;
      if(mode==="undone") return !done[it.id];
      if(mode==="key") return !!keySet[it.id];
      return true;
    });
    if(mode==="shuffle"){
      var arr=base.slice(); for(var i=arr.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var tmp=arr[i];arr[i]=arr[j];arr[j]=tmp;}
      return arr;
    }
    return base;
  }
  function answerIndex(it){
    var ans=String(it["答案"]||"").trim();
    if(/^[A-H]$/.test(ans)) return ans.charCodeAt(0)-65;
    if(it["选项"]&&it["选项"].length) return it["选项"].indexOf(ans);
    return -1;
  }
  function stats(){
    var doneN=Object.keys(done).length;
    $("nTotal").textContent=ALL.length;
    $("nDone").textContent=doneN;
    $("nLeft").textContent=list.length;
    $("nBasket").textContent=basket.length;
    renderBasket();
  }
  function renderBasket(){
    var box=$("basketList");
    if(!basket.length){ box.innerHTML='<span style="color:var(--sub)">暂无错题。做题时点「做错了·记入错题」即可入篮。</span>'; return; }
    var html="";
    basket.forEach(function(id){
      var it=null; ALL.forEach(function(x){ if(x.id===id) it=x; });
      if(!it) return;
      html+='<div><span>'+escHtml((it["题型"]||"")+" · "+it["题目"]).replace(/<span>.*?<\/span>/g,"")+'</span><button data-rm="'+id+'">移除</button></div>';
    });
    box.innerHTML=html;
    box.querySelectorAll("button[data-rm]").forEach(function(b){
      b.addEventListener("click",function(){ basket=basket.filter(function(x){return x!==b.getAttribute("data-rm");}); save(); reload(); stats(); });
    });
  }
  function show(){
    var box=$("card");
    if(!list.length){
      box.innerHTML='<div class="empty">当前范围没有题目。<br>换一个专题 / 模式，或点击「重置进度」重新开始。</div>';
      ["btnShowA","btnOK","btnNO","btnPrev","btnNext"].forEach(function(id){ var el=$(id); if(el) el.style.visibility="hidden"; });
      
      return;
    }
    ["btnShowA","btnOK","btnNO","btnPrev","btnNext"].forEach(function(id){ var el=$(id); if(el) el.style.visibility="visible"; });
    var it=list[idx];
    revealed=false; answered=false;
    var html='<div class="meta">';
    html+='<span class="tag qid">'+escHtml(it.id)+'</span><span class="tag">'+escHtml(it["专题"])+'</span><span class="tag">'+escHtml(it["题型"]||"")+'</span>'+((it["来源"]&&String(it["来源"]).indexOf("真题")>=0)?'<span class="tag src">'+escHtml(it["来源"])+'</span>':'');
    if(done[it.id]) html+='<span class="tag" style="background:rgba(82,196,26,0.14);color:#3E8C13;">已完成</span>';
    if(basket.indexOf(it.id)>=0) html+='<span class="tag" style="background:rgba(234,102,104,0.14);color:#B44244;">已入篮</span>';
    html+='</div>';
    if(it["材料"]) html+='<div class="material">'+markWords(it["材料"])+'</div>';
    if(IS_EN && clozeFullMode && it["passage"]){
      html+='<div class="material" style="border-left-color:#EAA7B2;max-height:300px;overflow-y:auto;">'+markWords(it["passage"])+'</div>';
    }
    html+='<div class="qtext">'+markWords(it["题目"])+'</div>';
    if(IS_EN && it["passage"]) html+='<div style="margin-bottom:10px;"><button id="btnPassage" style="background:#9BBBF4;color:#fff;border:none;border-radius:8px;padding:6px 14px;font-size:13px;cursor:pointer;">📖 查看本篇全文</button></div>';
    if(it["选项"]&&it["选项"].length){
      html+='<ul class="opts">';
      var letters="ABCDEFGH";
      it["选项"].forEach(function(o,i){
        html+='<li data-i="'+i+'"><span class="opt-letter">'+letters[i]+'</span>'+renderMath(String(o).replace(/^[A-Z][\.、]\s*/, ''))+'</li>';
      });
      html+='</ul>';
    } else if(it["题型"]==="单选"||it["题型"]==="多选"){
      html+='<div style="background:#FFF1F0;border:1px solid #FFCCC7;border-radius:8px;padding:10px 14px;margin:10px 0;font-size:13px;color:#CF1322;">⚠ 本题选项数据缺失（可能是早期存入时未保存选项）。建议删除此题后重新做题存入。</div>';
    }
    html+='<div class="feedback" id="fb"></div>';
    html+='<div class="answer" id="ans"></div>';
    html+='<div class="btns">';
    html+='<button id="btnShowA">显示答案 / 解析</button>';
    html+='<button id="btnOK" class="g" style="display:none;">做对了 ✔</button>';
    html+='<button id="btnNO" class="r" style="display:none;">做错了 · 记入错题</button>';
    html+='<button id="btnSkip">跳过</button>';
    html+='<button id="btnAITeach">AI 讲题</button>';
    html+='</div>';
    html+='<div class="nav"><button id="btnPrev">‹ 上一题</button><span style="font-size:12px;color:var(--sub);align-self:center;">'+(idx+1)+' / '+list.length+'</span><button id="btnNext">下一题 ›</button></div>';
    box.innerHTML=html;
    // 英语刷题：点击单词加入生词本
    if(IS_EN){
      box.querySelectorAll(".word-clickable").forEach(function(el){
        el.addEventListener("click", function(e){
          e.stopPropagation();
          var w=el.getAttribute("data-word");
          if(w && addShengci(w)){
            el.classList.add("word-saved");
          }
        });
      });
      // 完形填空：查看本篇全文
      var btnP=$("btnPassage");
      if(btnP) btnP.onclick=function(){ openPassage(it["passage"]); };
    }

    var ansBox=$("ans"), fb=$("fb");
    function renderAnswer(){
      var a="<div class='k'>答案："+renderMath(it["答案"])+"</div>";
      if(it["解析"]) a+="<br>"+renderMath(it["解析"]);
      if(it["来源"]&&String(it["来源"]).indexOf("真题")>=0) a+="<br><span style='color:var(--sub)'>来源："+escHtml(it["来源"])+"</span>";
      ansBox.innerHTML=a;
      ansBox.style.display="block";
    }
    function markOK(){
      done[it.id]=1; answered=true; save();
      // 同步更新复习进度：标记为已掌握，今日学习不再显示
      try{
        var rkey="__SUBJECT___cuowuji_v2";
        var rsaved=JSON.parse(localStorage.getItem(rkey)||"{}")||{};
        var rpm=rsaved.pm||{}, rst=rsaved.st||{}, rrv=rsaved.rv||{};
        var old=rpm[it.id]||{}, level=Math.min((Number(old.level)||0)+1,4);
        var days=[7,7,14,30,45][level];
        var now=new Date(); var y=now.getFullYear(), m=String(now.getMonth()+1).padStart(2,"0"), d=String(now.getDate()).padStart(2,"0");
        var today=y+"-"+m+"-"+d;
        var nd=new Date(now.getTime()+days*86400000);
        var next=nd.getFullYear()+"-"+String(nd.getMonth()+1).padStart(2,"0")+"-"+String(nd.getDate()).padStart(2,"0");
        rpm[it.id]={last:today,next:next,level:level};
        rst[it.id]="已掌握"; rrv[it.id]=today;
        localStorage.setItem(rkey,JSON.stringify({st:rst,rv:rrv,pm:rpm}));
      }catch(e){}
      fb.innerHTML="✔ 答对了"; fb.className="feedback ok"; fb.style.display="block";
      $("btnOK").style.display="none"; $("btnNO").style.display="none";
      if(basket.indexOf(it.id)>=0){ basket=basket.filter(function(x){return x!==it.id;}); save(); stats(); }
      stats();
    }
    function markNO(){
      if(basket.indexOf(it.id)<0) basket.push(it.id);
      done[it.id]=1; // 答错也算已完成（做过了），避免"只看未做"重复显示
      save(); stats();
      fb.innerHTML="已记入错题篮子（可点下方「存入错题本」批量入库）"; fb.className="feedback no"; fb.style.display="block";
      $("btnNO").style.display="none"; $("btnOK").style.display="none";
    }
    // 选择题作答
    var opts=box.querySelectorAll(".opts li");
    if(opts.length){
      var multi=(it["题型"]==="多选");
      if(multi){
        // 多选题：点选 toggle，提交时与答案集合比较
        opts.forEach(function(li){
          li.addEventListener("click",function(){
            if(answered||revealed) return;
            li.classList.toggle("sel");
          });
        });
        var subBtn=document.createElement("button");
        subBtn.id="btnSubmit"; subBtn.textContent="提交答案"; subBtn.className="m";
        var btns=box.querySelector(".btns");
        btns.insertBefore(subBtn, btns.firstChild);
        subBtn.addEventListener("click",function(){
          if(answered||revealed) return;
          var selSet=[];
          opts.forEach(function(o,i){ if(o.classList.contains("sel")) selSet.push(i); });
          var ans=String(it["答案"]||"").trim(), okSet=[];
          for(var k=0;k<ans.length;k++){ var c=ans.charCodeAt(k)-65; if(c>=0&&c<opts.length) okSet.push(c); }
          var correct=selSet.length===okSet.length && okSet.every(function(x){return selSet.indexOf(x)>=0;});
          opts.forEach(function(o,i){
            o.classList.remove("sel");
            if(okSet.indexOf(i)>=0) o.classList.add("right");
            else if(selSet.indexOf(i)>=0) o.classList.add("wrong");
          });
          if(correct){
            markOK(); renderAnswer();
          }else{
            fb.innerHTML="✘ 答错了，正确答案是 "+String(it["答案"])+"。"; fb.className="feedback no"; fb.style.display="block";
            revealed=true; answered=true; renderAnswer();
            $("btnNO").style.display="inline-block";
          }
        });
      }else{
      opts.forEach(function(li){
        li.addEventListener("click",function(){
          if(answered||revealed) return;
          var ai=answerIndex(it), sel=parseInt(li.getAttribute("data-i"),10);
          if(sel===ai){
            li.classList.add("right");
            fb.innerHTML="✔ 答对了！"; fb.className="feedback ok"; fb.style.display="block";
            revealed=true; answered=true; markOK();
            renderAnswer();
          }else{
            li.classList.add("wrong");
            opts.forEach(function(o){ if(parseInt(o.getAttribute("data-i"),10)===ai) o.classList.add("right"); });
            fb.innerHTML="✘ 答错了，正确答案是 "+String(it["答案"])+"。"; fb.className="feedback no"; fb.style.display="block";
            revealed=true; answered=true;
            renderAnswer();
            $("btnNO").style.display="inline-block";
          }
        });
      });
      }
      $("btnShowA").addEventListener("click",function(){
        if(revealed) return;
        revealed=true; renderAnswer();
        $("btnOK").style.display="inline-block";
        $("btnNO").style.display="inline-block";
      });
    }else{
      // 无选项题：显示答案后判定
      $("btnShowA").addEventListener("click",function(){
        if(revealed) return;
        revealed=true; renderAnswer();
        $("btnOK").style.display="inline-block";
        $("btnNO").style.display="inline-block";
      });
    }
    $("btnOK").addEventListener("click",markOK);
    $("btnNO").addEventListener("click",markNO);
    $("btnSkip").addEventListener("click",function(){ if(idx<list.length-1){idx++;show();} else {idx=0;show();} });
    $("btnPrev").addEventListener("click",function(){ idx=(idx-1+list.length)%list.length; show(); });
    $("btnNext").addEventListener("click",function(){ idx=(idx+1)%list.length; show(); });
    var aiBtn=$("btnAITeach");
    if(aiBtn) aiBtn.addEventListener("click",function(){
      var it=list[idx];
      if(!it){ showToast("暂无题目"); return; }
      var p="请帮我讲解这道专升本题目，讲清楚考点和解题思路：\n\n";
      p+="【题型】"+(it["题型"]||"")+"\n";
      p+="【题目】"+(it["题目"]||"")+"\n";
      if(it["材料"]) p+="【材料】"+it["材料"]+"\n";
      if(it["选项"]&&it["选项"].length){
        var L="ABCDEFGH";
        p+="【选项】\n"+it["选项"].map(function(o,i){ return L[i]+". "+o; }).join("\n");
      }
      p+="\n【答案】"+(it["答案"]||"")+"\n";
      if(it["解析"]&&it["解析"]!=="（本题未附解析）") p+="【解析】"+it["解析"]+"\n";
      p+="\n请分点讲解：1) 考点是什么；2) 为什么选这个答案；3) 其他选项错在哪。";
      if(window.AIAsk){ window.AIAsk(p, "AI讲题 · "+it.id); }
      else{ showToast("AI 助手未加载，请刷新页面"); }
    });
    stats();
  }
  function reload(){
    list=pool(); idx=0; show();
  }

  $("selTopic").addEventListener("change",reload);
  var selK2=$("selKaodian"); if(selK2) selK2.addEventListener("change",reload);
  $("btnShuffle").addEventListener("click",function(){setMode("shuffle");});
  $("btnOrder").addEventListener("click",function(){setMode("order");});
  $("btnUndone").addEventListener("click",function(){setMode("undone");});
  $("btnBasket").addEventListener("click",function(){setMode("basket");});
  $("btnKey").addEventListener("click",function(){setMode("key");});
  $("btnReset").addEventListener("click",function(){
    // 两次点击确认（避免原生弹窗在 file:// 下的不稳定）
    if(this._arm){
      done={}; basket=[]; nextId=BASE_QID; save();
      this._arm=false; this.textContent="重置进度";
      this.style.background=""; this.style.color="";
      showToast("已重置本学科刷题进度，正在刷新...");
      setTimeout(function(){ location.reload(); }, 500);
    }else{
      this._arm=true; this.textContent="再点一次确认重置";
      this.style.background="#EA6668"; this.style.color="#fff";
      var self=this;
      setTimeout(function(){ self._arm=false; self.textContent="重置进度"; self.style.background=""; self.style.color=""; }, 3000);
    }
  });
  $("btnClearBasket").addEventListener("click",function(){
    if(!basket.length) return;
    basket=[]; save(); reload(); stats();
  });
  // 导出
  function fmtDate(d){ return d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0"); }
  function buildExport(){
    var out="";
    basket.forEach(function(id){
      var it=null; ALL.forEach(function(x){ if(x.id===id) it=x; });
      if(!it) return;
      out+="## Q-"+String(nextId).padStart(3,"0")+"\n";
      out+="- 章节："+escHtml(it["章节"]||"99-综合")+"\n";
      out+="- 日期："+fmtDate(new Date())+"\n";
      out+="- 状态：待复习\n";
      out+="- 题型："+(it["题型"]||"选择")+"\n";
      var q=it["题目"]; if(it["材料"]) q=(it["材料"]+"\n\n"+q);
      out+="- 题目："+q+"\n";
      if(it["选项"]&&it["选项"].length){
        var letters="ABCDEFGH";
        var optsStr=it["选项"].map(function(o,i){return letters[i]+". "+o;}).join(" / ");
        out+="- 选项："+optsStr+"\n";
      }
      out+="- 答案："+it["答案"]+"\n";
      var jx=it["解析"]||"";
      if(it["来源"]&&String(it["来源"]).indexOf("真题")>=0) jx=(jx?jx+" ":"")+"（来源："+it["来源"]+"）";
      out+="- 解析："+jx+"\n\n";
      nextId++;
    });
    return out.trim();
  }
  function showManualExport(txt){
    var box=$("expBox"), ta=$("expText");
    ta.value=txt;
    box.style.display="block";
    ta.select();
    ta.setSelectionRange(0, txt.length);
    var copied=copyText(txt);
    basket=[]; save(); reload(); stats();
    showToast(copied ? "已复制到剪贴板。请粘贴到《错题本.md》末尾后运行 build.py。" :
      "错题文本已生成，请全选复制后粘贴到《错题本.md》末尾。", 6000);
  }
  $("btnExport").addEventListener("click",async function(){
    if(!basket.length){ showToast("错题篮子为空，先做题并把错题记入篮子。"); return; }
    var txt=buildExport();
    var button=this;
    button.disabled=true; button.textContent="正在存入…";
    // 构建本地错题JSON（手机APK/离线环境用）
    var localErrors=[];
    var todayStr=new Date().toISOString().slice(0,10);
    basket.forEach(function(qid){
      var it=ALL.find(function(x){return x.id===qid;});
      if(it){
        localErrors.push({
          id:"L-"+qid, 题目:it.题目||"", 选项:it.选项||[],
          答案:it.答案||"", 解析:it.解析||"",
          章节:it.章节||it.专题||"综合", 题型:it.题型||"单选",
          来源:it.来源||"题库", 状态:"待复习", 日期:todayStr
        });
      }
    });
    // 方式1：尝试server API（电脑端）
    var serverOk=false;
    try{
      var res=await fetch("/api/append-error", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({subject:"__SUBJECT__", text:txt})
      });
      var data=await res.json();
      if(res.ok){ nextId=parseInt(data.nextId,10)||nextId; serverOk=true; }
    }catch(e){}
    // 方式2：server成功则清空本地错题（已写入错题本.md）；失败才写入localStorage
    try{
      var lkey="__SUBJECT___errorbook_local";
      if(serverOk){
        localStorage.removeItem(lkey);
      }else{
        var existing=JSON.parse(localStorage.getItem(lkey)||"[]");
        localErrors.forEach(function(ne){
          // 按id去重：同一题累计错误次数，不同题即使答案相同也新增
          var found=existing.find(function(e){return e.id===ne.id;});
          if(found){ found.错误次数=(found.错误次数||1)+1; }
          else{ existing.push(ne); }
        });
        localStorage.setItem(lkey, JSON.stringify(existing));
      }
    }catch(e){}
    basket=[]; save(); reload(); stats();
    $("expBox").style.display="none";
    if(serverOk){
      showToast("已存入错题本，复习页已更新。", 4000);
    }else{
      showToast("已存入本地错题本（"+localErrors.length+"题），复习页自动读取。", 4000);
    }
    button.disabled=false; button.textContent="存入错题本";
  });
  // 初始
  setMode("shuffle");
})();
</script>
</body>
</html>
"""


def build_tiku(sub, base_qid):
    """生成学科根目录《题库页.html》。base_qid：错题本现有最大序号+1。"""
    d = sub["dir"].parent            # 学科根目录（题库.md 所在处）
    md = d / "题库.md"
    items = parse_tiku(md, sub["name"])
    mode = sub["mode"]
    katex_css = ""
    katex_js = ""
    if mode == "math":
        katex_css = '<link rel="stylesheet" href="../SCGSstudy/katex/katex.min.css">'
        katex_js = "../SCGSstudy/katex/katex.min.js"
    key_items = select_key_questions(sub["name"], items)
    html = (TIKU_HTML
            .replace("__KEY_JSON__", js_safe(key_items))
            .replace("__LABEL__", sub["label"])
            .replace("__COLOR__", sub["color"])
            .replace("__SUBJECT__", sub["name"])
            .replace("__TIKU_JSON__", js_safe(items))
            .replace("__BASE_QID_VAL__", str(base_qid))
            .replace("__SUBJECT___tiku", sub["name"] + "_tiku")
            .replace("__KATEX_CSS__", katex_css)
            .replace("__KATEX_JS__", katex_js)
            .replace("__INDEX__", "../SCGSstudy/index.html"))
    html = html.replace("var MATH = __MATH_MODE__;",
                        "var MATH = %s;" % ("true" if mode == "math" else "false"))
    html = html.replace("</body>", AI_HTML + SUBMIT_HTML + "\n</body>")
    out = d / "题库页.html"
    out.write_text(html, encoding="utf-8")
    return {"items": items, "out": out}


def build_index(per_subject, tiku_info):
    """生成统一入口 index.html（含各科统计 + 刷题入口）。"""
    cards = []
    for sub in SUBJECTS:
        info = per_subject[sub["name"]]
        cards.append("""
  <a class="sc" href="__REL__" style="--c:__COLOR__;">
    <div class="sc-icon">__ICON__</div>
    <div class="sc-name">__LABEL__</div>
    <div class="sc-desc">__DESC__</div>
    <div class="sc-stat" id="stat-__SUBJECT__">题数 __TOTAL__ · 待复习 __REVIEW__</div>
  </a>""".replace("__REL__", info["rel"])
            .replace("__COLOR__", sub["color"])
            .replace("__ICON__", sub["icon"])
            .replace("__LABEL__", sub["label"])
            .replace("__DESC__", sub["desc"])
            .replace("__SUBJECT__", sub["name"])
            .replace("__TOTAL__", str(info["total"]))
            .replace("__REVIEW__", str(info["review"])))
    tiku_cards = []
    for sub in SUBJECTS:
        t = tiku_info[sub["name"]]
        tiku_cards.append("""
  <a class="sc sc2" href="__REL__" style="--c:__COLOR__;">
    <div class="sc-icon">__ICON__</div>
    <div class="sc-name">__LABEL__ · 刷题库</div>
    <div class="sc-desc">答题判对错 · 做错一键入篮存入</div>
    <div class="sc-stat">共 __TOTAL__ 题</div>
  </a>""".replace("__REL__", "../%s/题库页.html" % sub["name"])
            .replace("__COLOR__", sub["color"])
            .replace("__ICON__", sub["icon"])
            .replace("__LABEL__", sub["label"])
            .replace("__TOTAL__", str(t["total"])))
    daily_data = []
    for sub in SUBJECTS:
        daily_data.append({
            "name": sub["name"], "label": sub["label"], "color": sub["color"],
            "rel": "../%s/错题集/复习页.html" % sub["name"],
            "items": [{key: item.get(key, "") for key in ("id", "章节", "错误次数", "最近复习", "日期", "状态")}
                      for item in per_subject[sub["name"]]["items"]],
        })
    quality = quality_check()
    word_cards = """
  <a class="sc sc2" href="../英语/错题集/单词本.html" style="--c:#9BBBF4;">
    <div class="sc-icon">EN</div>
    <div class="sc-name">英语 · 单词本</div>
    <div class="sc-desc">5210 词 · 翻卡记忆 · 标星生词 · 通用/四级区分</div>
    <div class="sc-stat">浏览 / 搜索 / 翻卡</div>
  </a>
  <a class="sc sc2" href="../英语/错题集/生词本.html" style="--c:#EAA7B2;">
    <div class="sc-icon">★</div>
    <div class="sc-name">英语 · 生词本</div>
    <div class="sc-desc">标星生词 + 手动记录 · 翻卡复习</div>
    <div class="sc-stat">导出 / 复制 W- 格式</div>
  </a>"""
    html = (INDEX_HTML
            .replace("__CARDS__", "\n".join(cards))
            .replace("__TIKU_CARDS__", "\n".join(tiku_cards))
            .replace("__WORD_CARDS__", word_cards)
            .replace("__DAILY_JSON__", js_safe(daily_data))
            .replace("__QUALITY_JSON__", js_safe(quality)))
    html = html.replace("</body>", AI_HTML + SUBMIT_HTML + "\n</body>")
    out = BASE / "index.html"
    out.write_text(html, encoding="utf-8")


INDEX_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#22304A">
<link rel="manifest" href="manifest.json?v=20260911">
<link rel="apple-touch-icon" href="icon-192.png">
<title>学习平台</title>
<style>
:root{--text:#1A1B1C;--sub:#6B7280;--bg:#F4F3EE;--card:#FFFFFF;--border:#E4E3DD;}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent;}
body{font-family:'Roboto','PingFang SC','Segoe UI',Arial,sans-serif;background:var(--bg);color:var(--text);padding:16px;line-height:1.6;}
.wrap{max-width:720px;margin:0 auto;}
h1{font-size:20px;font-weight:700;margin-bottom:2px;}
.sub{font-size:12px;color:var(--sub);margin-bottom:16px;}
.grid{display:flex;gap:12px;flex-wrap:wrap;}
.sc{flex:1 1 200px;background:var(--card);border:1px solid var(--border);border-radius:14px;padding:16px;text-decoration:none;color:var(--text);display:block;}
.sc:hover{border-color:var(--c);}
.sc.sc2{border-style:dashed;}
.sc-icon{width:38px;height:38px;border-radius:10px;background:var(--c);color:#22304A;font-weight:700;font-size:15px;display:flex;align-items:center;justify-content:center;margin-bottom:10px;}
.sc-name{font-size:16px;font-weight:700;margin-bottom:4px;}
.sc-desc{font-size:12px;color:var(--sub);margin-bottom:8px;}
.sc-stat{font-size:12px;font-weight:600;color:#33475C;}
.h2{font-size:13px;font-weight:700;margin:18px 0 8px;color:var(--sub);}
.note{font-size:12px;color:var(--sub);margin-top:20px;line-height:1.8;background:var(--card);border:1px dashed var(--border);border-radius:12px;padding:12px 14px;}
.daily-total{font-size:13px;color:var(--sub);margin-bottom:8px;}
.daily-total b{font-size:18px;color:var(--text);margin:0 3px;}
.daily-empty{font-size:12px;color:var(--sub);padding:10px 0;}
.daily-card{position:relative;}
.daily-count{font-size:20px;font-weight:700;margin:2px 0;}
.daily-focus{font-size:12px;color:var(--sub);}
.quality{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:12px 14px;margin-top:18px;font-size:12px;}
.quality-head{display:flex;justify-content:space-between;gap:8px;align-items:center;margin-bottom:8px;}
.quality-head strong{font-size:13px;}
.quality-ok{color:#3E8C13;font-weight:600;}
.quality-bad{color:#B44244;font-weight:600;}
.quality-list{margin-top:8px;max-height:260px;overflow:auto;}
.quality-list div{padding:4px 0;border-top:1px solid var(--border);}
.quality-list .error{color:#B44244;}
.quality-list .warning{color:#8A5B00;}
/* 移动端适配 */
@media (max-width:480px){
  .sc{min-height:80px;}
  .sc-name{font-size:15px;}
  .sc-stat{font-size:13px;}
}
</style>
</head>
<body>
<div class="wrap">
  <h1>学习平台</h1>
  <div style="background:rgba(250,173,20,0.12);border:1px solid rgba(250,173,20,0.35);border-radius:10px;padding:10px 14px;margin-bottom:14px;font-size:13px;color:#8C6D1F;line-height:1.7;">📌 学习数据（错题 / 复习进度 / 单词标记）保存在<b>本设备浏览器</b>中：清理浏览器缓存、更换设备或使用无痕模式会导致进度丢失。建议定期在「复习页 / 生词本」中使用<b>导出</b>功能备份。</div>
  <div class="h2">今日学习</div>
  <div class="daily-total">今天需要复习 <b id="dailyTotal">0</b> 题</div>
  <div class="grid" id="dailyList"></div>
  <div class="h2">错题复习</div>
  <div class="grid">__CARDS__
  </div>
  <div class="h2">题库刷题（做错 → 一键入篮 → 自动存入错题本）</div>
  <div class="grid">__TIKU_CARDS__
  </div>
  <div class="h2">英语单词</div>
  <div class="grid">__WORD_CARDS__
  </div>
  <div class="h2">共建题库</div>
  <div class="grid">
    <a href="contribute.html" class="card sc" style="text-decoration:none;color:inherit;display:block;">
      <div class="sc-icon" style="font-size:28px;">✍</div>
      <div class="sc-name" style="font-size:16px;font-weight:600;margin:6px 0;">贡献题目</div>
      <div class="sc-desc" style="font-size:12px;color:var(--sub);">填写题目 → 生成标准格式 → 复制发给站长 → 审核后加入题库</div>
    </a>
  </div>
  <div class="quality">
    <div class="quality-head"><strong>题库质量检查</strong><span id="qualitySummary"></span></div>
    <div id="qualitySubjects"></div>
    <div class="quality-list" id="qualityIssues"></div>
  </div>

</div>
<script>
window.__DAILY__ = __DAILY_JSON__;
window.__QUALITY__ = __QUALITY_JSON__;
(function(){
  var subjects=window.__DAILY__||[];
  function dateText(d){ return d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0"); }
  function today(){ return dateText(new Date()); }
  function due(item, plan){
    var next=plan[item.id]&&plan[item.id].next;
    return !next || next<=today();
  }
  var total=0, box=document.getElementById("dailyList");
  subjects.forEach(function(subject){
    // 合并本地存储的错题（手机APK/离线环境自动存入的）
    try{
      var _local=JSON.parse(localStorage.getItem(subject.name+"_errorbook_local")||"[]");
      if(_local.length){
        var _added=0;
        _local.forEach(function(le){
          // 按id去重：不同题目即使答案相同也保留
          var dup=subject.items.find(function(it){ return it.id===le.id; });
          if(dup) return;
          // 本地错题无选项时，从题库按题目内容相似度补全选项
          if(!le["选项"] || !le["选项"].length){
            var qShort=(le["题目"]||"").replace(/\s/g,"").slice(0,25);
            var match=subject.items.find(function(it){
              var itShort=(it["题目"]||"").replace(/\s/g,"").slice(0,25);
              return itShort&&qShort&&(itShort.indexOf(qShort)>=0||qShort.indexOf(itShort)>=0);
            });
            if(match&&match["选项"]&&match["选项"].length) le["选项"]=match["选项"].slice();
          }
          subject.items.push(le); _added++;
        });
        // 更新错题复习卡片的数字
        var statEl=document.getElementById("stat-"+subject.name);
        if(statEl&&_added){
          var baseTotal=subject.items.length;
          var baseReview=subject.items.filter(function(it){return it["状态"]!=="已掌握";}).length;
          statEl.textContent="题数 "+baseTotal+" · 待复习 "+baseReview+"（含本地"+_added+"题）";
        }
      }
    }catch(e){}
    var saved={};
    try{ saved=JSON.parse(localStorage.getItem(subject.name+"_cuowuji_v2")||"{}")||{}; }catch(e){}
    var plan=saved.pm||{}, dueItems=subject.items.filter(function(item){ return due(item,plan); });
    total+=dueItems.length;
    var chapters={};
    dueItems.forEach(function(item){ var chapter=item["章节"]||"未分类"; chapters[chapter]=(chapters[chapter]||0)+(Number(item["错误次数"])||0)+1; });
    var focus=Object.keys(chapters).sort(function(a,b){ return chapters[b]-chapters[a]; })[0]||"暂无到期题";
    var card=document.createElement("a");
    card.className="sc daily-card"; card.href=subject.rel+"?mode=due"; card.style.setProperty("--c",subject.color);
    card.innerHTML='<div class="sc-name">'+subject.label+' · 今日到期</div><div class="daily-count">'+dueItems.length+' 题</div><div class="daily-focus">优先：'+focus+'</div>';
    box.appendChild(card);
  });
  document.getElementById("dailyTotal").textContent=total;
  if(!subjects.length) box.innerHTML='<div class="daily-empty">暂无错题，先从题库开始练习。</div>';
})();
(function(){
  var report=window.__QUALITY__||{}, summary=report.summary||{};
  var total=(summary.errors||0)+(summary.warnings||0);
  var summaryBox=document.getElementById("qualitySummary");
  summaryBox.className=total?"quality-bad":"quality-ok";
  summaryBox.textContent=total?(summary.errors+" 个错误，"+summary.warnings+" 个提醒"):"未发现问题";
  document.getElementById("qualitySubjects").textContent=(report.subjects||[]).map(function(x){return x.name+"：错题"+x.errorBook+" 条，题库"+x.questionBank+" 题";}).join("　");
  var box=document.getElementById("qualityIssues");
  if(!total){ box.textContent="构建时间："+(report.generatedAt||""); return; }
  box.innerHTML=(report.issues||[]).slice(0,80).map(function(x){return '<div class="'+x.level+'">['+x.subject+'] '+x.source+' '+(x.item||"")+'：'+x.message+'</div>';}).join("");
})();
</script>
</body>
</html>
"""


def main():
    per = {}
    tiku_info = {}
    for sub in SUBJECTS:
        d = sub["dir"]
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
        items = build_review(sub)
        total = len(items)
        review = sum(1 for it in items if it.get("状态") != "已掌握")
        rel = "../%s/%s/复习页.html" % (sub["name"], "错题集")
        per[sub["name"]] = {"total": total, "review": review, "rel": rel, "items": items}
        print("[复习页] %-4s %d 题" % (sub["label"], total))
        if sub["name"] == "英语":
            words = build_wordcard(sub)
            book = build_wordbook(sub)
            manual = build_shengci(sub)
            print("[单词卡] 英语 %d 词" % len(words))
            print("[单词本] 英语 %d 词 · 生词本手动词 %d" % (len(book), manual))
        # 题库刷题页：base_qid = 错题本最大序号 + 1（导出错题时从这里续号）
        ids = [int(it["id"]) for it in items if it["id"].isdigit()]
        base_qid = (max(ids) + 1) if ids else 1
        t = build_tiku(sub, base_qid)
        tiku_info[sub["name"]] = {"total": len(t["items"])}
        print("[刷题页] %-4s %d 题 (导出序号起点 Q-%03d)" % (sub["label"], len(t["items"]), base_qid))
    build_index(per, tiku_info)
    print("已生成入口：%s" % (BASE / "index.html"))
    print("全部完成。")


if __name__ == "__main__":
    main()

