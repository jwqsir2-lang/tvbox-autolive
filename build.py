#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 zbds.top 的 IPTV4 直播列表转换成「老电视可用」的 TVBox 内嵌式配置。

为什么需要这一步：
  - 老电视（Android 4.x）走不了 https，而 live.zbds.top 的 http 地址会 301 到 https。
  - 远程列表方式老电视根本下载不下来，必须把频道内嵌进配置文件。
  - 只保留纯 http:// 明文流，https 流老电视解码也会失败。

输入：zbds 的 iptv4.txt（每行「频道名,url」，带 #genre# 分组标记）
输出：TVBox JSON，lives 全部是 {group, channels:[{name, urls}]} 内嵌结构
"""

import argparse
import json
import re
import ssl
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

# zbds 的 http 地址会 301 到 https，老电视访问不了；这两个镜像保持 https 但由
# GitHub Actions（海外 IP）去拉取，老电视只要打开最终生成的配置即可。
SOURCES = [
    ("zbds", "https://live.zbds.top/tv/iptv4.txt"),
    ("zbds", "https://gh-proxy.com/raw.githubusercontent.com/vbskycn/iptv/refs/heads/master/tv/iptv4.txt"),
    ("zbds", "https://raw.githubusercontent.com/vbskycn/iptv/refs/heads/master/tv/iptv4.txt"),
    ("supprise", "https://raw.githubusercontent.com/Supprise0901/TVBox_live/main/live.txt"),
    ("supprise", "https://gh-proxy.com/raw.githubusercontent.com/Supprise0901/TVBox_live/main/live.txt"),
]

# 只保留这些频道（白名单）。自动归类的正则会把县市级综合台、游戏轮播台、
# 点播伪直播混进来，老人用只需要主干频道，宁缺毋滥。
WHITELIST = {
    "央视": [f"CCTV{i}" for i in range(1, 18)]
    + [
        "CCTV5+", "CCTV4K", "CCTV8K",
        "CCTV1综合", "CCTV2财经", "CCTV3综艺", "CCTV4中文国际",
        "CCTV6电影", "CCTV7国防军事", "CCTV8电视剧", "CCTV9纪录",
        "CCTV10科教", "CCTV11戏曲", "CCTV12社会与法", "CCTV13新闻",
        "CCTV14少儿", "CCTV15音乐", "CCTV17农业农村",
        "CCTV怀旧剧场", "CCTV第一剧场", "CCTV文化精品", "CCTV风云剧场",
        "CCTV兵器科技", "CCTV女性时尚", "CCTV台球", "CCTV卫生健康",
        "CCTV高尔夫网球", "CCTV风云音乐", "CCTV风云足球", "CCTV中视购物",
        "CCTV证券资讯", "CCTV中学生", "CCTV国学", "CCTV世界地理",
        "CCTV摄影", "CCTV书画", "CCTV宝物", "CCTV老故事", "CCTV发现之旅",
        "CCTV新科动漫", "CCTV数码时代", "CCTV职业指南", "CCTV央广购物",
        "CCTV戏曲", "CCTV电影", "CCTV电视剧", "CCTV音乐", "CCTV纪录",
        "CCTV新闻", "CCTV财经", "CCTV中文国际", "CCTV少儿", "CCTV农业农村",
        "CCTV社会与法", "CCTV综艺", "CCTV综合", "CCTV科教",
    ],
    "卫视": [
        "北京卫视", "东方卫视", "湖南卫视", "浙江卫视", "江苏卫视",
        "安徽卫视", "山东卫视", "广东卫视", "深圳卫视", "四川卫视",
        "重庆卫视", "贵州卫视", "云南卫视", "河南卫视", "湖北卫视",
        "江西卫视", "辽宁卫视", "黑龙江卫视", "吉林卫视", "陕西卫视",
        "山西卫视", "福建卫视", "东南卫视", "广西卫视", "甘肃卫视",
        "青海卫视", "宁夏卫视", "新疆卫视", "西藏卫视", "内蒙古卫视",
        "河北卫视", "天津卫视", "上海卫视", "三沙卫视", "兵团卫视",
        "中国农林卫视", "厦门卫视", "延边卫视", "大湾区卫视", "安多卫视",
        "南方卫视", "旅游卫视", "海峡卫视", "四川卫视4K", "东方卫视4K",
    ],
    "新闻": ["CCTV4欧洲", "CCTV4美洲", "CCTV4亚洲", "CGTN", "TVBS新闻", "TVB无线新闻", "中国蓝新闻"],
    "体育": ["CCTV5", "CCTV5+", "CCTV风云足球", "CCTV高尔夫网球", "CCTV台球", "体育休闲频道", "四海钓鱼"],
    "影视": [
        "CHC电影", "CHC动作电影", "CHC影迷电影", "CHC家庭影院", "CCTV电影",
        "东方影视", "北京影视", "上海电视剧", "广东影视", "江苏影视",
        "动作电影", "电影频道", "家庭影院", "东森电影", "TVB千禧经典",
    ],
    "纪录": [
        "CCTV9", "CCTV世界地理", "CCTV发现之旅", "CCTV老故事", "CCTV摄影",
        "CCTV宝物", "CCTV茶", "CCTV国学", "CCTV书画", "CCTV文化精品",
        "发现之旅", "人与自然", "地理中国", "之江纪录",
    ],
    "少儿": [
        "CCTV14", "CCTV少儿", "优漫卡通", "优漫卡通频道", "金鹰卡通",
        "北京卡酷", "嘉佳卡通", "哈哈炫动", "CCTV新科动漫", "CCTV中学生",
        "浙江少儿", "中学生", "经典动画大集合",
    ],
    "音乐": ["CCTV15", "CCTV音乐", "CCTV风云音乐", "音乐频道"],
    "三农": ["CCTV17", "CCTV农业农村", "中国农林卫视", "农林卫视", "CCTV农业"],
}

GROUP_ORDER = ["央视", "卫视", "新闻", "体育", "影视", "纪录", "少儿", "音乐", "三农"]

# 同一频道的多种写法归一，合并线路
NAME_MERGE = {
    "CCTV1综合": "CCTV1", "CCTV2财经": "CCTV2", "CCTV3综艺": "CCTV3",
    "CCTV4中文国际": "CCTV4", "CCTV6电影": "CCTV6", "CCTV7国防军事": "CCTV7",
    "CCTV8电视剧": "CCTV8", "CCTV9纪录": "CCTV9", "CCTV10科教": "CCTV10",
    "CCTV11戏曲": "CCTV11", "CCTV12社会与法": "CCTV12", "CCTV13新闻": "CCTV13",
    "CCTV14少儿": "CCTV14", "CCTV15音乐": "CCTV15", "CCTV17农业农村": "CCTV17",
    "四川卫视4K": "四川卫视", "东方卫视4K": "东方卫视",
}

LINES_PER_CHANNEL = 3       # 每个频道最多保留几条备播线路
PROBE_TIMEOUT = 6           # 单条流探活超时（秒）
PROBE_WORKERS = 32


def normalize(name: str) -> str:
    """频道名归一：去空格/括号注释/高清HD后缀，方便白名单匹配。"""
    n = name.strip()
    n = re.sub(r"\(.*?\)|（.*?）|\[.*?\]|【.*?】", "", n)
    n = n.replace("　", " ")
    n = n.replace("高清", "").replace("HD", "").replace(" ", "").replace("-", "").upper()
    return NAME_MERGE.get(n, n)


def fetch_list(url: str) -> str:
    """下载直播列表文本。用空 ProxyHandler 走直连。"""
    ctx = ssl._create_unverified_context()
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ctx),
    )
    req = urllib.request.Request(url, headers={"User-Agent": "okhttp/4.9.1"})
    with opener.open(req, timeout=25) as r:
        return r.read().decode("utf-8", "ignore")


def parse_txt(text: str):
    """解析「频道名,url」文本，返回 [(频道名, url)]。"""
    out = []
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or "," not in line:
            continue
        name, url = line.split(",", 1)
        url = url.strip().split("$")[0]
        if url.startswith("http"):
            out.append((name.strip(), url))
    return out


def probe(item):
    """探活单条流：能读到响应体且像 m3u8/媒体流就算可用，同时返回耗时。"""
    import time
    name, url = item
    t0 = time.time()
    try:
        ctx = ssl._create_unverified_context()
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}),
            urllib.request.HTTPSHandler(context=ctx),
        )
        req = urllib.request.Request(url, headers={"User-Agent": "okhttp/4.9.1"})
        data = opener.open(req, timeout=PROBE_TIMEOUT).read(1024)
        ok = b"#EXTM3U" in data or len(data) > 300
        return (name, url, round(time.time() - t0, 2), bool(ok))
    except Exception:
        return (name, url, round(time.time() - t0, 2), False)


def filter_and_group(items):
    """白名单过滤 + 归一 + 分组。返回 {组名: {频道名: [(延迟,url,原名)]}}。"""
    want = {}
    for group, names in WHITELIST.items():
        for n in names:
            want[normalize(n)] = group

    by = {}
    for name, url in items:
        key = normalize(name)
        group = want.get(key)
        if not group:
            continue
        if not url.startswith("http://"):      # 老电视只要 http 明文流
            continue
        by.setdefault(group, {}).setdefault(key, []).append((99.0, url, name))
    return by


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="base.json", help="基础配置（含 sites/parses/flags 的原配置）")
    ap.add_argument("--out", default="tvbox.json", help="输出配置")
    ap.add_argument("--no-probe", action="store_true", help="跳过实测，直接收下全部 http 流")
    args = ap.parse_args()

    # 1) 拉取直播列表（多源 + 多镜像容灾，全部合并，不命中即停）
    items = []
    pulled = 0
    for source, url in SOURCES:
        try:
            text = fetch_list(url)
            items.extend(parse_txt(text))
            pulled += 1
            print(f"[拉取] OK {url} ({len(text)} 字节)")
        except Exception as e:
            print(f"[拉取] 失败 {url}: {type(e).__name__} {e}")
    if not items:
        print("[错误] 所有源都拉取失败", file=sys.stderr)
        return 1
    print(f"[解析] 合并 {pulled} 个源，共 {len(items)} 条频道记录")

    # 2) 白名单过滤
    by = filter_and_group(items)
    total = sum(len(v) for v in by.values())
    print(f"[过滤] 白名单命中 {total} 个频道")

    # 3) 实测可用性（默认开启，--no-probe 可跳过）
    if not args.no_probe:
        todo = []
        for group in by.values():
            for name, urls in group.items():
                todo.extend((name, u) for _, u, _ in urls)
        print(f"[实测] 开始探测 {len(todo)} 条流 ...")
        alive = set()
        speed = {}
        with ThreadPoolExecutor(PROBE_WORKERS) as ex:
            for name, url, latency, ok in ex.map(probe, todo):
                if ok:
                    alive.add((name, url))
                    speed[(name, url)] = latency
        before = sum(sum(len(v) for v in g.values()) for g in by.values())
        for group in by.values():
            for name in group:
                group[name] = [(speed.get((name, u), 99.0), u, orig)
                               for _, u, orig in group[name]
                               if (name, u) in alive]
                group[name] = [t for t in group[name] if t[0] < 99.0]
        after = sum(sum(len(v) for v in g.values()) for g in by.values())
        print(f"[实测] 可用 {after}/{before} 条")

    # 4) 每频道取最快的 N 条，组装成 lives 内嵌分组
    groups = []
    for gname in GROUP_ORDER:
        if gname not in by:
            continue
        channels = []
        for cname, urls in sorted(by[gname].items()):
            urls = sorted(set(urls), key=lambda x: x[0])[:LINES_PER_CHANNEL]
            if not urls:
                continue
            display = NAME_MERGE.get(cname, cname)
            channels.append({
                "name": display,
                "urls": [f"{u}$线路{i+1}" for i, (_, u, _) in enumerate(urls)],
            })
        if channels:
            groups.append({"group": gname, "channels": channels})

    n_ch = sum(len(g["channels"]) for g in groups)
    n_url = sum(len(c["urls"]) for g in groups for c in g["channels"])
    print(f"[组装] {len(groups)} 组 / {n_ch} 频道 / {n_url} 条线路")

    # 5) 合并到基础配置
    with open(args.base, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["lives"] = groups
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print(f"[输出] {args.out}（{groups and len(groups)} 组，已保留原 sites/parses/flags）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
