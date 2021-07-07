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
from nonebot import on_command, on_message
from nonebot import permission as su
from nonebot.adapters.cqhttp import Bot, Event, unescape, permission, MessageSegment
from nonebot.rule import to_me, Rule
from nonebot.typing import T_State


# 去除词汇
remove_word = ['', '词云']
# 忽略其他机器人
bot_qq = [2825814139,2373378824]

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


def chat_word_cloud() -> Rule:
    async def _chat_word_cloud(bot: "Bot", event: "Event", state: T_State) -> bool:
        if event.__getattribute__('message_type') == 'private':
            return False
        else:
            return True

    return Rule(_chat_word_cloud)


record_message = on_message(rule=chat_word_cloud(), permission=None, handlers=None, temp=False, priority=1, block=False,
                            state=None, state_factory=None)


def remove_cqcode(msg: str) -> str:
    msg = unescape(str(msg))
    return re.sub('\[.*?\]', '', msg)


@record_message.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    msg = remove_cqcode(event.__getattribute__("message"))

    if msg and event.self_id != event.user_id:
        write_csv(str(event.group_id), [
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            f'{event.user_id}\n',
            msg
        ])


WORD_CLOUD = on_command('wordcloud',
                        aliases={"词云"},
                        rule=to_me(),
                        priority=5
                        )
MY_WORD_CLOUD = on_command('mywordcloud',
                           aliases={"我的词云"},
                           rule=to_me(),
                           priority=5
                           )


def read_csv(csv_name: str, user_id: str = None):

    res = []
    with open(f'data{os.sep}{csv_name}', 'r', encoding="utf-8-sig", newline="") as f:
        jieba.load_userdict(
            f'data{os.sep}wordcloud_bot{os.sep}dict{os.sep}mydict.txt')
        jieba.analyse.set_stop_words(
            f'data{os.sep}wordcloud_bot{os.sep}stopwords{os.sep}all_stopwords.txt')
        csv_list = list(csv.reader(f))
        csv_list.pop(0)
        for x in csv_list:
            if user_id and not re.search(user_id, x[1]):
                continue
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


@MY_WORD_CLOUD.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    await MY_WORD_CLOUD.send('开始生成，请稍后')
    if event.__getattribute__('message_type') == 'private':
        await MY_WORD_CLOUD.finish('请在群组中使用！')

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
    try:
        words = read_csv(csv_name=f'{event.group_id}.csv', user_id=str(event.user_id))
    except:
        words = []
    if words:
        w.generate(" ".join(words))
        img_base64 = get_pic_base64(w.to_image())
        await MY_WORD_CLOUD.finish(MessageSegment.image(file=f'base64://{img_base64}'))
    else:
        await MY_WORD_CLOUD.finish('还没有记录呢！')


@WORD_CLOUD.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    await WORD_CLOUD.send('开始生成，请稍后')
    if event.__getattribute__('message_type') == 'private':
        await WORD_CLOUD.finish('请在群组中使用！')

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
    try:
        words = read_csv(csv_name=f'{event.group_id}.csv')
    except:
        words = []
    if words:
        w.generate(" ".join(words))
        img_base64 = get_pic_base64(w.to_image())
        await MY_WORD_CLOUD.finish(MessageSegment.image(file=f'base64://{img_base64}'))
    else:
        await MY_WORD_CLOUD.finish('还没有记录呢！')
