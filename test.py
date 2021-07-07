import base64
import os
import csv
import os
import re
import time
from io import BytesIO
from typing import List

import jieba
import jieba.analyse
import wordcloud
import imageio


# 创建csv文件
def create_csv(name: str, head: List[str]):
    with open(name, 'w', encoding="utf-8-sig", newline="") as f:
        csv_write = csv.writer(f)
        csv_head = head
        csv_write.writerow(csv_head)


# 向csv文件写入单行记录
def write_csv(name: str, data_row):
    if not os.path.exists("data"):
        os.mkdir("data")
    full_name = f'{name}'
    path = f"data{os.sep}{full_name}.csv"
    if not os.path.exists(path):
        # 创建记录表
        create_csv(name=path, head=["date", "qq", "message"])

    # 写入记录
    with open(path, 'a+', encoding="utf-8-sig", newline="") as f:
        csv_write = csv.writer(f)
        csv_write.writerow(data_row)


def read_csv(csv_name: str):
    remove_word = ['', '词云']
    res = []
    with open(f'data{os.sep}{csv_name}', 'r', encoding="utf-8-sig", newline="") as f:
        jieba.load_userdict(
            f'data{os.sep}wordcloud_bot{os.sep}dict{os.sep}mydict.txt')
        jieba.analyse.set_stop_words(
            f'data{os.sep}wordcloud_bot{os.sep}stopwords{os.sep}all_stopwords.txt')
        csv_list = list(csv.reader(f))
        csv_list.pop(0)
        for x in csv_list:
            x[2] = re.sub(
                "(https?|ftp|file)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]", "", x[2])
            # word = jieba.lcut(x[2])
            word = jieba.analyse.extract_tags(x[2])
            for x in word:
                if x in remove_word:
                    continue
                res.append(x)
    return res


# 将图片转化为 base64
def get_pic_base64(content) -> str:
    if not content:
        return ""
    elif isinstance(content, bytes):
        image_buffer = BytesIO(content)
    elif isinstance(content, BytesIO):
        image_buffer = content
    else:
        image_buffer = BytesIO()
        content.save(image_buffer, format='png')
    res = str(base64.b64encode(image_buffer.getvalue()), encoding="utf-8")
    return res


# 像素不能超过 178956970
# mk = imageio.imread("4.png")
# image_colors = wordcloud.ImageColorGenerator(mk)
w = wordcloud.WordCloud(width=300,
                        height=300,
                        background_color='white',
                        font_path=f'data{os.sep}wordcloud_bot{os.sep}msyh.ttc',
                        # mask=mk,
                        scale=15,
                        # color_func=image_colors,
                        # max_font_size=30
                        )
w.generate(" ".join(read_csv(f'130516740.csv')))
# img_base64 = get_pic_base64(w.to_image())
w.to_file('all4.png')
