import base64
import csv
import os
import re
import time
from io import BytesIO
from typing import List

import httpx
import jieba
import jieba.analyse
import wordcloud
from nonebot import on_command, on_message
from nonebot.adapters.cqhttp import Bot, Event, unescape, MessageSegment
from nonebot.plugin import on_keyword
from nonebot.rule import to_me, Rule
from nonebot.typing import T_State

# 去除词汇
remove_word = ['', '词云']
# 忽略其他机器人
bot_qq = [2825814139, 2373378824]


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
        if event.__getattribute__('message_type') == 'private' or event.user_id in bot_qq or event.is_tome():
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
    msg = re.sub('(https?|ftp|file)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]', '', msg)
    msg = re.sub('我的词云|词云', '', msg)
    if msg and event.self_id != event.user_id:
        write_csv(str(event.group_id), [
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            f'{event.user_id}\n',
            msg
        ])


WORD_CLOUD = on_keyword({'群词云'},
                        # aliases={"词云"},
                        rule=to_me(),
                        priority=4,
                        block=True
                        )
MY_WORD_CLOUD = on_keyword({'我的词云'},
                           # aliases={"我的词云"},
                           rule=to_me(),
                           priority=4,
                           block=True
                           )


async def read_csv(csv_name: str, user_id: str = None, _type: str = None):
    async with httpx.AsyncClient(proxies={}) as client:
        try:
            mydict = await client.get(
                'https://cdn.jsdelivr.net/gh/Quan666/QQGroupWordCloud/data/wordcloud_bot/dict/mydict.txt')
            all_stopwords = await client.get(
                'https://cdn.jsdelivr.net/gh/Quan666/QQGroupWordCloud/data/wordcloud_bot/stopwords/all_stopwords.txt')
            with open(f'data{os.sep}wordcloud_bot{os.sep}dict{os.sep}mydict.txt', 'w', encoding='utf-8') as f:
                f.write(mydict.text)
            with open(f'data{os.sep}wordcloud_bot{os.sep}stopwords{os.sep}all_stopwords.txt', 'w',
                      encoding='utf-8') as f:
                f.write(all_stopwords.text)
        except Exception as e:
            print(e)
    res = []
    with open(f'data{os.sep}{csv_name}', 'r', encoding="utf-8-sig", newline="") as f:
        jieba.load_userdict(
            f'data{os.sep}wordcloud_bot{os.sep}dict{os.sep}mydict.txt')
        jieba.analyse.set_stop_words(
            f'data{os.sep}wordcloud_bot{os.sep}stopwords{os.sep}all_stopwords.txt')
        csv_list = list(csv.reader(f))
        csv_list.pop(0)
        for x in csv_list:
            # 群友词云
            if user_id and not re.search(user_id, x[1]):
                continue
            if is_continue(_type=_type, data_row=x): continue
            x[2] = re.sub(
                "(https?|ftp|file)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]", "", x[2])
            # word = jieba.lcut(x[2])
            word = jieba.analyse.extract_tags(x[2])
            for x in word:
                if x in remove_word:
                    continue
                res.append(x)
    return res


# 是否跳过循环
def is_continue(_type: str, data_row) -> bool:
    if _type and _type == 'today':
        today = time.mktime(time.strptime(f"{time.strftime('%Y-%m-%d', time.localtime())} 0:0:0", "%Y-%m-%d %H:%M:%S"))
        old = time.mktime(time.strptime(data_row[0], "%Y-%m-%d %H:%M:%S"))
        if today >= old:
            return True
    if _type and _type == 'yesterday':
        today = time.mktime(time.strptime(f"{time.strftime('%Y-%m-%d', time.localtime())} 0:0:0", "%Y-%m-%d %H:%M:%S"))
        yesterday = today - 60 * 60 * 24
        old = time.mktime(time.strptime(data_row[0], "%Y-%m-%d %H:%M:%S"))
        if yesterday >= old or old > today:
            return True


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


def get_type(args: str) -> str:
    if args and re.search('今日|今天', args):
        return 'today'
    if args and re.search('昨日|昨天', args):
        return 'yesterday'


@MY_WORD_CLOUD.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.message).strip()
    _type = get_type(args)
    await MY_WORD_CLOUD.send('开始生成，请稍候')
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
        words = await read_csv(csv_name=f'{event.group_id}.csv', user_id=str(event.user_id), _type=_type)
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
    args = str(event.message).strip()
    _type = get_type(args)
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
        words = await read_csv(csv_name=f'{event.group_id}.csv', _type=_type)
    except:
        words = []
    if words:
        w.generate(" ".join(words))
        img_base64 = get_pic_base64(w.to_image())
        await WORD_CLOUD.finish(MessageSegment.image(file=f'base64://{img_base64}'))
    else:
        await WORD_CLOUD.finish('还没有记录呢！')
