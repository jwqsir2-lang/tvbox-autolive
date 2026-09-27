# TVBox 自动直播配置（老电视适用）

电视端直接用这个地址（复制粘贴到 TVBox 的「配置地址」里）：

```
http://raw.githubusercontent.com/jwqsir2-lang/tvbox-autolive/main/tvbox.json
```

## 说明

- **78 个频道**（央视 12 / 卫视 36 / 新闻 / 体育 / 影视 / 纪录 / 少儿 / 音乐 / 三农），182 条线路
- 所有播放地址都是 **http:// 明文流**，Android 4.x 老电视可用（暴风 TV40X 实测通过）
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
| `build.py` | 生成脚本（GitHub Actions 跑的） |
| `base.json` | 基础配置（站点/解析/flags，直播部分为空） |
