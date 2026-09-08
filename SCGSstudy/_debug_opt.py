# -*- coding: utf-8 -*-
"""调试版本：检查英语题库选项行处理"""
import sys
sys.path.insert(0, r'D:\专升本学习\SCGSstudy')

# 直接导入build.py中的函数
import importlib.util
spec = importlib.util.spec_from_file_location("build", r"D:\专升本学习\SCGSstudy\build.py")
build = importlib.util.module_from_spec(spec)

# 重写split_options添加调试
original_split_options = None

def debug_split_options(line):
    print(f'  [split_options] 输入: {repr(line[:80])}')
    result = original_split_options(line)
    print(f'  [split_options] 输出: {result} (数量={len(result)})')
    return result

spec.loader.exec_module(build)
original_split_options = build.split_options
build.split_options = debug_split_options

# 解析英语题库
from pathlib import Path
items = build.parse_tiku(Path(r'D:\专升本学习\英语\题库.md'), '英语')

print(f'\n总题数: {len(items)}')

# 检查前5道单选题的选项
single_count = 0
for it in items:
    if it.get('题型') == '单选':
        single_count += 1
        if single_count <= 5:
            print(f'\n--- {it["id"]} ---')
            print(f'题目: {it.get("题目", "")[:60]}')
            print(f'选项数: {len(it.get("选项", []))}')
            print(f'选项: {it.get("选项", [])}')

print(f'\n单选题总数: {single_count}')
