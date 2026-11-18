# Daily Outfit Lookbook

一个 WorkBuddy / Claude Skills 技能：把「我的照片 + 我的衣柜 + 我收藏的灵感图」变成每日 5 套
可直接穿、可直接买的穿搭方案页。

不是凭空生成模特图——**每一套都由你已有的或已收藏的单品组出来**，缺的那件才标成「建议补」。

## 它解决什么问题

大多数 AI 穿搭建议的问题是：图上好看，但你衣柜里没有、也不知道该买哪一件。
这个技能倒过来做：

1. 先读你的真实照片，搞清你的脸型、发色、肤色、身材比例、**以及你实际在穿的颜色**；
2. 再读你的衣柜截图（淘宝收藏 / 已购），把每件单品变成可检索的条目，带当时价格；
3. 从灵感库里**只借手法**（撞色、叠穿、黑色收口），不借具体单品；
4. 组出 5 套覆盖不同场景的方案，每件单品标注来源：`已有` / `衣柜收藏` / `建议补`；
5. 用固定的奶油色棚拍底图做「换装不换人」，边缘虚化掉镜框线，输出一张自包含的 HTML 页面。

## 效果预览

页面结构（单文件 HTML，图片 base64 内嵌）：

```
每日穿搭 · 5 套上身方案
├── 个人风格画像（色板 + 身材要点）
├── Look 1  上身效果图 │ 命名 / 场景标签 / 灵感借鉴
│                     │ 单品表：名称+来源徽章 | 版型要求 | 淘宝搜索直链
├── Look 2 ...
└── Look 5 ...
```

## 安装

```bash
git clone https://github.com/xinqin700-arch/daily-outfit-lookbook.git
cp -R daily-outfit-lookbook ~/.workbuddy/skills/
```

依赖：Python 3 + Pillow。

```bash
pip install pillow
```

## 使用

在 WorkBuddy 里直接说：

- 「按我的照片和衣柜，做今天 5 套搭配」
- 「生成我的上身效果图 + 单品链接」
- 「每天早 8 点推 5 套穿搭」

技能会按 `SKILL.md` 里的流程执行。手动跑脚本：

```bash
# 1. 边缘虚化（输入换装原图，输出 look_1..N.jpg）
python scripts/blur_edges.py work/2026-11-18/raw work/2026-11-18/wear --prefix look

# 2. 渲染页面（配置格式见 examples/looks.example.json）
python scripts/build_lookbook.py looks.json lookbook-2026-11-18.html
```

## 目录结构

```
daily-outfit-lookbook/
├── SKILL.md                        # 工作流与护栏
├── scripts/
│   ├── blur_edges.py               # 裁镜框线 + 高斯渐变 + 压缩
│   └── build_lookbook.py           # looks.json → 自包含 HTML
├── references/
│   ├── style-profiling.md          # 怎么从三类素材里提取风格与来源标注
│   └── prompt-templates.md         # 换装提示词模板与角色一致性方法
└── examples/
    └── looks.example.json          # 配置示例
```

## 两个关键结论（踩过坑才有的）

**1. 不要把用户真实照片喂进图生图换装。**
试过 high fidelity、锁定构图、只换单件衣服三种写法，模型每次都会重画脸——人物就变了。
可靠做法是**参考链**：先定一张基础人像，之后每套都以它为 `image1`，只改服装段落。
这样整组图看起来像同一天拍的同一场 shoot。

**2. 衣柜截图是「想买」，不是「已有」。**
来源徽章搞错，这个页面的价值就归零了。判断标准：照片里出现过的 = 已有；
截图里出现的 = 收藏（带价格）；两边都没有的 = 建议补。

## 隐私

技能本身不包含任何人物图片或用户素材。真实照片与由其生成的基础人像请留在本地
`work/` 目录，不要提交到公开仓库。

## License

MIT-0
