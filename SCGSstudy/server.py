#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本机错题本服务：提供页面，并把题库导出的错题直接写入 Markdown。"""
import json
import pathlib
import re
import subprocess
import sys
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build


ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD = ROOT / "SCGSstudy" / "build.py"
ERROR_BOOKS = {
    "计算机": ROOT / "计算机" / "错题集" / "错题本.md",
    "高数": ROOT / "高数" / "错题集" / "错题本.md",
    "英语": ROOT / "英语" / "错题集" / "错题本.md",
}


def next_question_id(path):
    """返回现有错题本中最大 Q 序号的下一个值（排除 HTML 注释块内的模板示例）。"""
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    ids = [int(value) for value in re.findall(r"^##\s*Q-(\d+)\s*$", text, re.M)]
    return max(ids, default=0) + 1


def question_blocks(text):
    """返回 Markdown 中每道错题的文本区块及其位置。"""
    comments = [(match.start(), match.end()) for match in re.finditer(r"<!--.*?-->", text, re.S)]
    headers = [
        header for header in re.finditer(r"^##\s*Q-\d+\s*$", text, re.M)
        if not any(start <= header.start() < end for start, end in comments)
    ]
    blocks = []
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        blocks.append((header.start(), end, text[header.start():end].strip()))
    return blocks


def field_value(block, field):
    """读取单个字段；题干允许有换行，以便阅读材料也参与去重。"""
    pattern = r"(?ms)^-\s*%s\s*[:：]\s*(.*?)(?=^-\s*[^:：]+\s*[:：]|\Z)" % re.escape(field)
    match = re.search(pattern, block)
    return match.group(1).strip() if match else ""


def question_fingerprint(block):
    """以题干和选项识别同一道题，忽略空白符与大小写差异。"""
    question = field_value(block, "题目")
    options = field_value(block, "选项")
    if not question:
        return ""
    normalize = lambda value: re.sub(r"\s+", "", value).casefold()
    return normalize(question) + "|" + normalize(options)


def update_field(block, field, value):
    """替换区块内单行字段；字段不存在时追加。"""
    pattern = r"(?m)^-\s*%s\s*[:：]\s*.*$" % re.escape(field)
    replacement = "- %s：%s" % (field, value)
    updated, count = re.subn(pattern, replacement, block, count=1)
    return (updated if count else block.rstrip() + "\n" + replacement).rstrip() + "\n"


def with_original_spacing(original, start, end, updated):
    """替换字段时保留原题块末尾的空行格式。"""
    suffix = re.search(r"\s*$", original[start:end]).group(0)
    return updated.rstrip() + (suffix or "\n")


def merge_or_append(book, exported):
    """合并重复错题并追加新题，返回新增数和合并次数。"""
    original = book.read_text(encoding="utf-8") if book.exists() else ""
    existing = {}
    for start, end, block in question_blocks(original):
        fingerprint = question_fingerprint(block)
        if fingerprint and fingerprint not in existing:
            existing[fingerprint] = (start, end, block)

    updates = {}
    additions = []
    for _, _, block in question_blocks(exported):
        fingerprint = question_fingerprint(block)
        if fingerprint and fingerprint in existing:
            updates[fingerprint] = updates.get(fingerprint, 0) + 1
        else:
            additions.append(block)
            if fingerprint:
                existing[fingerprint] = (None, None, block)

    text = original
    replacements = []
    for fingerprint, increase in updates.items():
        start, end, block = existing[fingerprint]
        old_count = field_value(block, "错误次数")
        try:
            next_count = int(old_count) + increase
        except ValueError:
            next_count = increase
        updated = update_field(block, "错误次数", str(next_count))
        updated = update_field(updated, "日期", __import__("datetime").date.today().isoformat())
        updated = update_field(updated, "状态", "待复习")
        replacements.append((start, end, with_original_spacing(original, start, end, updated)))
    for start, end, replacement in sorted(replacements, reverse=True):
        text = text[:start] + replacement + text[end:]

    if additions:
        first_id = next_question_id(book)
        counter = iter(range(first_id, first_id + len(additions)))
        added_text = "\n\n".join(additions)
        added_text = re.sub(r"^## Q-\d+", lambda _: "## Q-%03d" % next(counter), added_text, flags=re.M)
        text = text.rstrip() + "\n\n" + added_text + "\n"
    book.write_text(text, encoding="utf-8", newline="\n")
    return len(additions), sum(updates.values())


def update_review_record(book, question_id, reason, increment=False):
    """把复习时选择的错因写回原题，并可累计一次新的失误。"""
    original = book.read_text(encoding="utf-8") if book.exists() else ""
    target = None
    for start, end, block in question_blocks(original):
        if re.search(r"^##\s*Q-%s\s*$" % re.escape(str(question_id)), block, re.M):
            target = (start, end, block)
            break
    if target is None:
        raise ValueError("没有找到这道错题")
    start, end, block = target
    updated = update_field(block, "错因", reason)
    updated = update_field(updated, "日期", __import__("datetime").date.today().isoformat())
    updated = update_field(updated, "状态", "待复习")
    if increment:
        try:
            count = int(field_value(block, "错误次数") or 0) + 1
        except ValueError:
            count = 1
        updated = update_field(updated, "错误次数", str(count))
    text = original[:start] + with_original_spacing(original, start, end, updated) + original[end:]
    book.write_text(text, encoding="utf-8", newline="\n")



class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format, *args):
        # 保留一行简洁日志，避免正常刷题时终端输出过多。
        print("[服务] " + format % args)

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/sync"):
            try:
                data = {}
                for sub_name, sub_dir in [("计算机", "计算机"), ("高数", "高数"), ("英语", "英语")]:
                    tiku_path = ROOT / sub_dir / "题库.md"
                    items = build.parse_tiku(tiku_path, sub_name)
                    data[sub_name] = {"tiku": items, "count": len(items)}
                wordbook_path = ROOT / "英语" / "错题集" / "单词本.md"
                words = build.parse_wordbook(wordbook_path)
                data["英语"]["words"] = words
                data["英语"]["word_count"] = len(words)
                import datetime
                data["synced_at"] = datetime.datetime.now().isoformat()
                self.send_json(HTTPStatus.OK, data)
            except Exception as exc:
                print("[服务] 同步失败：", exc)
                self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})
            return
        super().do_GET()

    def do_POST(self):
        if self.path not in ("/api/append-error", "/api/update-review"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 200_000:
                raise ValueError("提交内容大小不正确")
            data = json.loads(self.rfile.read(size).decode("utf-8"))
            subject = data.get("subject")
            if subject not in ERROR_BOOKS:
                raise ValueError("提交内容不正确")

            if self.path == "/api/update-review":
                question_id = str(data.get("id") or "").strip()
                reason = str(data.get("reason") or "").strip()
                if not re.fullmatch(r"\d+", question_id) or not reason or len(reason) > 30:
                    raise ValueError("复习记录不正确")
                update_review_record(ERROR_BOOKS[subject], question_id, reason, bool(data.get("increment")))
                self.send_json(HTTPStatus.OK, {"saved": True})
                return

            exported = data.get("text")
            if not isinstance(exported, str):
                raise ValueError("提交内容不正确")
            exported = exported.strip()
            headers = re.findall(r"^##\s*Q-\d+\s*$", exported, re.M)
            if not headers or not exported.startswith("## Q-"):
                raise ValueError("错题格式不正确")

            book = ERROR_BOOKS[subject]
            added, merged = merge_or_append(book, exported)

            try:
                subprocess.run([sys.executable, str(BUILD)], cwd=str(ROOT), check=True)
            except subprocess.CalledProcessError:
                self.send_json(HTTPStatus.OK, {
                    "saved": True,
                    "nextId": next_question_id(book), "added": added, "merged": merged,
                    "error": "错题已存入，但复习页更新失败。",
                })
                return
            self.send_json(HTTPStatus.OK, {
                "nextId": next_question_id(book), "added": added, "merged": merged,
            })
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except Exception as exc:
            print("[服务] 写入失败：", exc)
            self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "保存失败，请稍后重试。"})


def main():
    address = ("0.0.0.0", 8765)
    server = ThreadingHTTPServer(address, Handler)
    url = "http://127.0.0.1:8765/%E9%94%99%E9%A2%98%E6%9C%AC/index.html"
    print("错题本已启动：" + url)
    # 自动获取局域网IP
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
    except Exception:
        lan_ip = "<电脑IP>"
    print("局域网访问：http://%s:8765/SCGSstudy/index.html" % lan_ip)
    print("手机连同一WiFi后，浏览器打开上面的地址")
    print("此窗口保持打开即可；关闭窗口会停止自动入库。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n错题本服务已停止。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

