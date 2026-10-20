# 自动直播配置

电视端直接用这个地址：

```
http://raw.githubusercontent.com/jwqsir2-lang/tvbox-autolive/main/tvbox.json
```

## 说明
：

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
