# 自动直播配置

电视端直接用这个地址：

```
http://raw.githubusercontent.com/jwqsir2-lang/tvbox-autolive/main/tvbox.json
```

## 说明

- **78 个频道**（央视 12 / 卫视 36 / 新闻 / 体育 / 影视 / 纪录 / 少儿 / 音乐 / 三农），182 条线路
- 所有播放地址都是 **http:// 明文流**，Android 4.x 老电视可用
- 频道直接内嵌在配置里，打开直播**不需要联网下载列表**，秒开
- GitHub Actions 每 6 小时自动重新生成一次（拉取 zbds + supprise 最新直播源）

## 源失效后怎么更新

某天大部分台播不动了，去仓库的 **Actions** 页面：

1. 左侧选「自动更新直播配置」
2. 点右上角「Run workflow」→ 绿色按钮确认
3. 等 10 秒左右，重新下载 `tvbox.json` 即可

也可以重新打开本页复制上面的地址，文件会自动覆盖。

## 要传到自己网站空间

从仓库下载 [`tvbox.json`](./tvbox.json)，上传到 serv00 空间的 `public_html` 目录，
然后电视端地址换成 `http://你的域名/tvbox.json`。

## 文件

| 文件 | 作用 |
|---|---|
| `tvbox.json` | 最终配置（电视端用这个） |

==============================================================================
最终订阅 tvbox.json 由 build.py 在 GitHub Actions 里每 6 小时重新生成，直播源全部来自 两个上游（共 5 个拉取地址，全部尝试、合并去重）：

1. zbds（直播湾） — 实际原始仓库是 vbskycn/iptv

https://live.zbds.top/tv/iptv4.txt（主源）
https://raw.githubusercontent.com/vbskycn/iptv/refs/heads/master/tv/iptv4.txt
https://gh-proxy.com/raw.githubusercontent.com/vbskycn/iptv/refs/heads/master/tv/iptv4.txt（gh-proxy 镜像，国内 Actions 拉取容灾）
2. supprise — Supprise0901/TVBox_live

https://raw.githubusercontent.com/Supprise0901/TVBox_live/main/live.txt
https://gh-proxy.com/.../Supprise0901/TVBox_live/main/live.txt（同上镜像）
生成流程：拉取 5 个地址 → 合并 → 按白名单过滤（央视/卫视/新闻/体育/影视/纪录/少儿/音乐/三农 9 组）→ 只保留 http:// 明文流（https 老电视解码会失败）→ 与 base.json（站点/解析/flags）合并写出 tvbox.json。

两点值得注意：

upstream 的 zbds 源本身是 vbskycn/iptv 这个 GitHub 仓库，live.zbds.top 只是它的分发域名。所以真正的源头是两个 GitHub 仓库：vbskycn/iptv 和 Supprise0901/TVBox_live，哪天它们停更，这个订阅也就失效了。
workflow 实际跑的是 build.py --no-probe，即跳过了流可用性实测，每频道是按源里原始顺序取前 N 条 (LINES_PER_CHANNEL)，不是按延迟排序——README 说的「182 条线路」是未探测直接收下的
