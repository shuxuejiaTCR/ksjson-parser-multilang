#!/bin/python
# -*- coding: utf-8 -*-
#
# 修改说明：配合新版 readjson.py。
# 如果 extract/text/lang0/, lang1/... 存在，说明是多语言文件，
# 会依次把每种语言的翻译写回 origin_json['scenes'][i]['texts'][j][1][lang_index]。
# 如果没有 lang{N} 子目录（旧的单语言情况），行为跟原脚本完全一样。

import json
import os
import sys
import time

scr_dir = os.path.split(os.path.realpath(__file__))[0]
os.chdir(scr_dir)

json_file_list = []
with open('./jsonlist.txt', 'rt', encoding = 'utf-8') as f:
    json_file_list = f.read().splitlines(False)


def get_lang_count_on_disk(filename):
    """看 extract/text/ 下有几个 lang{N} 子目录，返回其数量（0 表示单语言旧布局）。"""
    n = 0
    while os.path.exists('./extract/text/lang%d/%s' % (n, filename)):
        n += 1
    return n


def file_was_modified(filename, cutoff_mtime):
    lang_count = get_lang_count_on_disk(filename)
    if lang_count == 0:
        p = './extract/text/' + filename
        return os.path.exists(p) and os.path.getmtime(p) > cutoff_mtime
    for lang_index in range(lang_count):
        p = './extract/text/lang%d/%s' % (lang_index, filename)
        if os.path.getmtime(p) > cutoff_mtime:
            return True
    return False


if not os.path.exists('./last_write_time.txt'):
    modified_list = json_file_list
else:
    cutoff = os.path.getmtime('./last_write_time.txt')
    modified_list = filter(lambda i: file_was_modified(i, cutoff), json_file_list)

new_write = False
for filename in modified_list:
    with open('./json/' + filename, 'rt', encoding = 'utf-8') as f:
        origin_json = json.load(f)

    lang_count = get_lang_count_on_disk(filename)
    single_lang = (lang_count == 0)
    lang_range = [0] if single_lang else list(range(lang_count))

    for lang_index in lang_range:
        if single_lang:
            text_dir = './extract/text/'
            select_dir = './extract/select/'
        else:
            text_dir = './extract/text/lang%d/' % lang_index
            select_dir = './extract/select/lang%d/' % lang_index

        with open(text_dir + filename, 'rt', encoding = 'utf-8') as f:
            user_text_json = json.load(f)
        with open(select_dir + filename, 'rt', encoding = 'utf-8') as f:
            user_select_json = json.load(f)

        for ujson_index, ujson_val in enumerate(user_text_json):
            if ujson_val != None:
                olist = origin_json['scenes'][ujson_index]['texts']
                for ulist_index, ulist_val in enumerate(ujson_val):
                    otext_index = ulist_index // 2
                    is_character = (ulist_index % 2 == 0)
                    otext = olist[otext_index]
                    if isinstance(otext[1], list):
                        idx = lang_index if lang_index < len(otext[1]) else 0
                        if is_character:
                            otext[1][idx][0] = ulist_val
                        else:
                            otext[1][idx][1] = ulist_val
                    else:
                        # 单语言条目：只有 lang_index == 0 时才有意义
                        if lang_index == 0:
                            if is_character:
                                otext[1] = ulist_val
                            else:
                                otext[2] = ulist_val
        for ujson_index, ujson_val in enumerate(user_select_json):
            if ujson_val != None:
                origin_json['scenes'][ujson_index]['selects'] = ujson_val

    with open('./json/' + filename, 'wt', encoding = 'utf-8') as f:
        json.dump(origin_json, f, ensure_ascii = False, indent = None)
        print(filename + ' write DONE!', file = sys.stderr)
        new_write = True

if not new_write:
    print('No file updated, have a good day!', file = sys.stderr)
else:
    with open('./last_write_time.txt', 'wt', encoding = 'utf-8') as f:
        f.write(time.asctime())
        print('Write time updated.', file = sys.stderr)
