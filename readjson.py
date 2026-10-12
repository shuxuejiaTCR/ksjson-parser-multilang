#!/bin/python
# -*- coding: utf-8 -*-
#
# 修改说明：
# 原脚本只提取 otext[1] 列表中的第 0 个语言 (otext[1][0])。
# 当一条文本 otext[1] 是列表时，其中每个元素 [character, text]
# 对应游戏内的一种语言；本版本会遍历所有语言，
# 分别输出到 extract/text/lang{N}/ 和 extract/select/lang{N}/ 下
# （N 从 0 开始）。如果某个 scn 文件实际上只有单一语言
# （otext[1] 不是 list），行为和原脚本保持一致，
# 仍然写到 extract/text/ 和 extract/select/ 根目录，不建子目录。

import json
import os
import sys
import time

src_dir = os.path.split(os.path.realpath(__file__))[0]
os.chdir(src_dir)


def format(elem):
    def format_inner(elem):
        i, val = elem
        val = json.dumps(val, ensure_ascii = False)
        return val if i % 2 == 0 else '  ' + val

    if elem == None:
        return '\n  null'
    else:
        return '\n  [\n    ' + ',\n    '.join(list(map(format_inner, enumerate(elem)))) + '\n  ]'


def get_lang_count(otext):
    """otext[1] 是 list 时，list 的长度就是这条文本包含的语言数量。"""
    if isinstance(otext[1], list):
        return len(otext[1])
    return 1


def get_char_text(otext, lang_index):
    """取出某条文本在指定语言下的 (character, text)。

    如果这条文本本身语言数量比文件里最多的语言数量少
    （理论上不应该发生，但保险起见做个兜底），就退回用第 0 个语言。
    """
    if isinstance(otext[1], list):
        idx = lang_index if lang_index < len(otext[1]) else 0
        character = otext[1][idx][0] or otext[0]
        text = otext[1][idx][1]
    else:
        character = otext[1] or otext[0]
        text = otext[2]
    return character, text


json_file_list = []
with open('./jsonlist.txt', 'rt', encoding = 'utf-8') as f:
    json_file_list = f.read().splitlines(False)

modified_list = None
if not os.path.exists('./last_extract_time.txt'):
    modified_list = json_file_list
else:
    modified_list = filter(lambda i: os.path.getmtime('./json/' + i) > os.path.getmtime('./last_extract_time.txt'), json_file_list)

new_extract = False
for filename in modified_list:
    with open('./json/' + filename, 'rt', encoding = 'utf-8') as f:
        origin_json = json.load(f)

    # 先扫一遍这个文件里出现过的最大语言数量
    lang_count = 1
    for ojson_val in origin_json['scenes']:
        if 'texts' in ojson_val:
            for otext in ojson_val['texts']:
                lang_count = max(lang_count, get_lang_count(otext))

    for lang_index in range(lang_count):
        user_text = []
        user_select = []

        for ojson_index, ojson_val in enumerate(origin_json['scenes']):
            if 'texts' in ojson_val:
                while len(user_text) <= ojson_index:
                    user_text.append(None)
                user_text[ojson_index] = []
                for otext in ojson_val['texts']:
                    character, text = get_char_text(otext, lang_index)
                    user_text[ojson_index].append(character)
                    user_text[ojson_index].append(text)
            if 'selects' in ojson_val:
                while len(user_select) <= ojson_index:
                    user_select.append(None)
                user_select[ojson_index] = ojson_val['selects']

        if lang_count == 1:
            text_dir = './extract/text/'
            select_dir = './extract/select/'
        else:
            text_dir = './extract/text/lang%d/' % lang_index
            select_dir = './extract/select/lang%d/' % lang_index
        os.makedirs(text_dir, exist_ok = True)
        os.makedirs(select_dir, exist_ok = True)

        format_str = '[' + ','.join(list(map(format, user_text))) + '\n]'
        with open(text_dir + filename, 'wt', encoding = 'utf-8') as f:
            f.write(format_str)
        with open(select_dir + filename, 'wt', encoding = 'utf-8') as f:
            json.dump(user_select, f, ensure_ascii = False, indent = 2)

    print(filename + ' extract DONE! (%d language%s)' % (lang_count, 's' if lang_count > 1 else ''), file = sys.stderr)
    new_extract = True

if not new_extract:
    print('No file updated, have a good day!', file = sys.stderr)
else:
    with open('./last_extract_time.txt', 'wt', encoding = 'utf-8') as f:
        f.write(time.asctime())
        print('Extract time updated.', file = sys.stderr)
