# 《静谧田园》 Switch 简体中文汉化补丁

<p align="center">
  <img src="switch_icons/icon_SimplifiedChinese.png" alt="静谧田园 Switch 简体中文封面图标" width="180" height="180">
</p>

<p align="center">
  <b>Nintendo Switch《静谧田园 / ほの暮しの庭 / Village in the Shade》全量 100% 简体中文本地化工程</b><br>
  Atmosphere LayeredFS 实机免改包补丁 · 霞鹜文楷等宽 32px 掌机大字号 · 官方简中矢量切片重定向 · 413 项 FAD 贴图封包无损重构
</p>

<p align="center">
  <a href="README.md"><b>简体中文</b></a> | <a href="README_EN.md"><b>English</b></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Nintendo%20Switch-e60012.svg?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/TitleID-01001BA027DD8000-0078d7.svg?style=flat-square" alt="TitleID">
  <img src="https://img.shields.io/badge/Game%20Version-v1.3.0%20(v458752)-brightgreen.svg?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/Translation%20Status-100%25%20(56%2C747%20Lines)-success.svg?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/QA%20Gate-294%2F294%20Batches%20Passed-blue.svg?style=flat-square" alt="QA">
  <img src="https://img.shields.io/badge/Font-LXGW%20WenKai%20Mono%20v1.530-orange.svg?style=flat-square" alt="Font">
  <img src="https://img.shields.io/badge/Runtime-Atmosphere%20LayeredFS%20%2F%20Eden-9cf.svg?style=flat-square" alt="Runtime">
</p>

---

## 📖 项目背景与概述 (Overview)

《静谧田园》（ほの暮しの庭 / Village in the Shade）是一款充满和风民俗风情与神怪幻想的慢节奏乡村生活角色扮演游戏。
原版 Nintendo Switch 亚洲发行版本仅提供了日文与港台繁体中文支持，且存在以下诸多痛点：
1. **繁中台词台湾腔与生硬机翻感严重**：句尾泛滥使用“囉/喔/耶/唷/捏/咧”，角色人设（孤傲少女帷、严肃村长林、随和市井六角）严重扁平化；
2. **掌机字号过小**：官方移植将对话字体由日文原版的 32px 缩减至 26px，在 Switch 720p 掌机屏幕上字符渲染高度不足 17px，阅读极其费眼吃力；
3. **小地图与大量 UI 图集未汉化**：18 个小地图地名及主菜单版权标示烘焙在图集中，在繁中版下依然无法得到妥善本地化；
4. **字体缺失与错位**：字库覆盖不全，且 ASCII 半角字符与全角汉字排版参差不齐。

**本项目实现了该游戏在 Nintendo Switch 平台上的 100% 全量高品质简体中文本地化**。通过逆向游戏引擎渲染视口、FAFULLFS 虚拟文件系统、NVN Tegra Block Linear 贴图机制以及 FAD 贴图描述符链，为玩家带来原汁原味、契合中国大陆现代语言规范的极佳游玩体验。

---

## ✨ 核心特性与技术突破 (Key Features)

### 1. 100% 全量文本汉化与深度人设校正 (100% Full Translation)
- **全域覆盖**：涵盖系统 UI、世界观设施、动植物特产、任务教学、神话典籍、制作人名单、全道具说明以及全剧情日常对话共 **294 个批次、56,747 行对照文本**（含 v1.3.0 全部 14 位村民生日新增剧情、生日设定任务、新道具、新信件与更新文本）；
- **神怪区分与代词规范**：严格恪守“**古神尊称用祂/祂们，普通妖怪动物用它/它们或他/他们**”，一票否决繁体代词“妳”与“牠”；
- **全量脱繁入简**：对繁体语气词与港台口语残留进行全量专项治理（彻底剔除违和的“啰/喔/耶/唷/捏/咧”，规范“咖哩 $\rightarrow$ 咖喱”）；
- **立体人设还原**：今野的阴阳怪气拖长音（`～`）、六角的热情市井口癖（`～っス` $\rightarrow$ “……呐/哟/喽”）、帷的孤傲带刺冷感、木珠的断续呢喃等均得到深度还原。

### 2. 掌机 1.2 倍舒适大字增强版与引擎级垂直居中校准 (Handheld 1.2x Scaled Font & Baseline Alignment)
- 逆向查明官方移植时中文对话（`FONT_ID_GAME_TALK`）与通用 UI（`FONT_ID_GAME`）从日版原生 32px 强行缩至 26px（字符面积萎缩 34%）；
- 证实引擎底层拥有 `枠内に収めるための拡縮处理`（文本超长自动水平微挤压 Auto-Fit）；
- **全域升级 1.2 倍大字版**：以日版原生字号为基准全面放大 1.2 倍（大标题 `46px`、主 UI/对话 `38px`、书籍/小字 `29px`），字符渲染面积提升超 110%，在 Switch 掌机 720p 屏幕上清晰舒适、彻底告别费眼阅读；
- **逆向攻关消除基线下沉 Bug**：深入逆向 `village.exe` 字体渲染管线，直接调节 `font.dat` 原生全局 `offsetY` 偏移，消除了官方繁中槽位遗留的 4px 下沉缺陷，实现交互提示（`Ⓐ 岔路的祠堂`）、底部操作栏（`Ⓡ 转向`）全场景毫米级完美居中。

### 3. 官方 PC 级正统字库 —— 霞鹜文楷等宽 (LXGW WenKai Mono)
- 选用 **霞鹜文楷等宽 (LXGW WenKai Mono v1.530) Medium (500)**（1:1 契合 PC 官方版视觉骨架，兼顾掌机 720p 与电视 1080p 抗锯齿）；
- **全字符集覆盖**：拥有 46,946+ 个字符覆盖，彻底杜绝任何冷门汉字或物产名缺字豆腐块（□）；
- **等宽（Mono）精细排版**：严格保证 ASCII 半宽（0.5 em）与全角汉字（1.0 em）对齐，彻底消除对话框与表格数据跳字/错位隐患；
- 提供 `--weight regular`（400 纤细常规体）与 `--weight medium`（500 推荐加粗体）双模式支持。

### 4. 0 字节封包膨胀的小地图与贴图矢量重定向 (Zero-Expansion Texture Routing)
- 小地图 18 个地名切片（水车小屋、樟树诊所等）原烘焙在大贴图封包中；
- 本项目逆向解析 `texture.dat` 与 `framework_texture.dat`，直接修改贴图切片 UV 寻址，将其无缝重定向到官方 PC 简中矢量图元流；
- **在 0 字节体积膨胀的前提下，达成 18 处小地图地名与主菜单版权标示的原生级简体中文显示！**

### 5. UI 贴图封包无损重构与四大致命缺陷攻坚 (UI Texture Repacking)
- 攻克 `data/fairy/resident_lang_tc.fad` 的 413 个贴图描述符链（64B 前导描述符 + 128B NMPLTEX1 头 + 20B YKCMP_V1 容器 + NVN Tegra Swizzle 贴图数据）及动态排布新增的 `resident_v130.fad`（5.13 MB）；
- **彻底攻坚四大导致实机卡死/崩溃的 P0 缺陷**：
  1. **P0-1 压缩长度定义偏差**：修正 YKCMP 容器与 NMPLTEX1 头部少算 20 字节 YK 头导致实机 LZ4 解压 100% 崩溃的根本死因；
  2. **P0-2 贴图像素格式对齐**：为 61 张专用格式贴图升级描述符为标准 BC3（`0x07`）并严格同步解压尺寸；
  3. **P0-3 Tegra Swizzle 块高适配**：动态读取 `ints[14] & 0xFF` 适配 Block Height Log2 模式（标题艺术字 Logo #211 正确使用 `mode=3`），彻底杜绝画面撕裂花屏；
  4. **P0-4 FAD 主索引表绝对偏移脱节**：重打包时逐项重算并同步 `0xd00` 起的 413 项主贴图查找表绝对物理偏移与步长，彻底攻克“卡在加载第一帧”的 Unmapped 内存访问死锁！
- 涵盖标题艺术字 Logo《静谧田园》、主菜单开始/设定按钮、库存详情弹窗、分类标签、31 张新闻传单看板等共计 **66 张**本土化贴图图集。

### 6. Switch 桌面图标与 NACP 简体元数据 (Custom Icon & NACP)
- 将《静谧田园》简体中文标题与发行商写入 Control NACP 的 Slot 13（繁中）与 Slot 14（简中），并自动同步 `config.ini` 中的版本号为 `1.3.0`；
- 配套提供高清重绘的 Switch 桌面封面图标（`icon.jpg`），支持 Atmosphere 插件 `sys-tweak` / `sys-icon` 动态加载，实机开机即见精美简中封面。

### 7. 严苛的自动化流水线质检门禁 (Automated Quality Gate)
- 门禁脚本 `tools/validate_batch.py` 对全量 294 个批次执行 **8 大多维审查**：
  1. JSON 结构与字段拓扑完整性；
  2. 行文本非空性；
  3. 内联控制标签（`<player>`, `<icon ...>`, `<color=...>` 等）100% 与日文原文比对；
  4. 字库码位全覆盖检查；
  5. 繁体字形与港台违禁词一票否决；
  6. 日式直角引号 `「」` 拦截与大陆规范引号强制转换；
  7. 视口排版超宽预警。
- **当前状态**：294/294 批次 **0 Error / 0 Warning，100% 完美通过！**

---

## 📥 补丁下载与安装指南 (Installation Guide)

### 适用版本与环境
- **游戏本体**：Nintendo Switch《ほの暮しの庭 / 靜謐田園 / Village in the Shade》
- **适用版本**：Base + Update `v1.3.0`（内部版本号 `v458752`，向下兼容 v1.2.0）
- **TitleID**：`01001BA027DD8000`

---

### 方法一：实机 Atmosphere (大气层) 部署
1. 关机取出 Switch 的 TF / MicroSD 卡（或通过 DBI 的 MTP 模式连接电脑）；
2. 进入本项目的产物目录 `output/atmosphere`（或解压最新的分发包 `静谧田园简体中文补丁-v1.3.0.zip`）；
3. 将 `atmosphere` 文件夹直接复制并合并覆盖到 Switch TF 卡的根目录下：
   ```text
   SDCard:/
   └── atmosphere/
       └── contents/
           └── 01001BA027DD8000/
               ├── icon.jpg                          # (可选: sys-tweak 桌面图标)
               ├── config.ini                        # (sys-icon 桌面游戏名与版本号拦截配置)
               ├── control/                          # (NACP 控制元数据备份)
               │   ├── control.nacp
               │   ├── icon_SimplifiedChinese.dat
               │   └── icon_TraditionalChinese.dat
               └── romfs/data/
                   ├── database/                     # (核心: 47 个本地化数据表与 32px 字体配置)
                   │   ├── talk.dat
                   │   ├── item.dat
                   │   ├── font.dat
                   │   └── ... (共 47 个文件，22.93 MB)
                   ├── misc_1_00.dat                 # (核心: 霞鹜文楷等宽字库归档 164.36 MB)
                   └── fairy_1_00.dat                # (可选: 全量 UI 贴图图集 1.212 GB)
   ```
4. 将 TF 卡插回 Switch，启动 Atmosphere 进入游戏即可享受 100% 简体中文！

> [!TIP]
> **桌面图标显示说明**：  
> Atmosphere 原生 LayeredFS 机制仅对 `romfs/` 生效。若要在 Switch 官方主菜单看到简体中文图标与游戏名，请在 Switch TF 卡上安装 Atmosphere 常用插件 **`sys-tweak`** 或 **`sys-icon`**，开机即会自动读取 `icon.jpg`。

---

### 方法二：PC 模拟器挂载 (Eden / Ryujinx / Yuzu)

#### Eden 模拟器
1. 打开 Eden 模拟器 Mod 挂载目录：
   `%APPDATA%\eden\load\01001BA027DD8000\Village_SC_Translation\`
2. 将 `output/atmosphere/contents/01001BA027DD8000/romfs/` 文件夹直接拷贝至上述路径下；
3. 启动 Eden 模拟器，加载游戏 Base NSP 即可秒进游戏，实测 0 报错稳定运行。

#### Ryujinx (龙神模拟器)
1. 在 Ryujinx 游戏列表中，右键点击游戏并选择 **Open Atmosphere Mods Directory**；
2. 新建名为 `Village_SC_Translation` 的文件夹；
3. 将补丁目录中的 `romfs` 完整复制放入；
4. 重启模拟器运行游戏。

---

## 🛠️ 工具链与开发者快速上手 (CLI Cheat-Sheet)

本项目提供了一套完全自动化、跨平台的 Python 工具链，位于 `tools/` 目录下。

### 1. 运行自动化质检门禁 (Validate Batches)
```powershell
# 校验全部 294 个批次（必须保持 0 Error / 0 Warning）
python tools/validate_batch.py all

# 校验单个批次
python tools/validate_batch.py batch_004_sys_ui.json
```

### 2. 编译实机数据库补丁 (Build Database Patch)
```powershell
# 编译全部 47 个二进制数据库（含文本、多行、外观、小地图贴图重定向及 32px 掌机字号）
python tools/build_patch.py
```

### 3. 编译字库归档 (Build Font Archive)
```powershell
# 采用默认推荐的 Medium 500 字重（1:1 契合 PC 原版加粗排版）
python tools/build_font_patch.py

# 采用 Regular 400 纤细常规字重
python tools/build_font_patch.py --weight regular
```

### 4. 编译 UI 贴图图集 (Build Fairy Texture Archive)
```powershell
# 全量路线 B：66 张贴图全量重打包升级为 BC3（包含艺术字 Logo、按钮、作物弹窗与传单看板）
python tools/build_fairy_patch.py --mode all

# 极稳路线 A：仅替换 5 张原生 0x07 BC3 贴图（艺术字 Logo 与 4 张大传单）
python tools/build_fairy_patch.py --mode safe
```

### 5. 替换 Switch 桌面图标与 NACP 控制元数据 (Apply Control Patch)
```powershell
python tools/apply_control_patch.py
```

### 6. 查看翻译进度与专项扫描 (Status & Calibration)
```powershell
# 查看整体批次翻译与质检状态
python tools/batch_status.py

# 专项扫描代词、神魔判定、动词态助词“著”与角色口癖
python tools/scan_calibration_targets.py
```

---

## 📂 项目目录结构 (Repository Layout)

```text
Village-SC/
├── docs/                                     # 专项技术与本地化规范文档
│   ├── ARCHITECTURE.md                       # 底层架构、7 槽位机制、FAD 与 Swizzle 逆向手册
│   ├── BUILD_GUIDE.md                        # 工具链编译、实机 Atmosphere 与模拟器挂载指南
│   ├── LOCALIZATION_GUIDE.md                 # 翻译规范、代词神魔判定、语气词与人设口癖红线
│   ├── CRASH_AUDIT.md                        # 实机报错排查与四大 P0 级致命缺陷深度归因报告
│   └── NON_MAINLAND_AUDIT.md                 # 港台腔词汇与非大陆用法全量排查报告
├── output/                                   # 编译生成的实机 LayeredFS 补丁交付产物
│   └── atmosphere/contents/01001BA027DD8000/
│       ├── icon.jpg                          # sys-tweak 桌面动态替换图标
│       ├── control/                          # NACP 控制元数据与图标备份
│       └── romfs/data/
│           ├── database/                     # 47 个本地化 .dat 数据库 (含 32px 字体与小地图路由)
│           ├── misc_1_00.dat                 # 霞鹜文楷等宽 v1.530 字库归档 (164.36 MB)
│           └── fairy_1_00.dat                # 全量 66 张贴图重打包图集 (1.08 GB)
├── switch_icons/                             # Switch 桌面简体中文封面图标 (PNG / JPG)
├── tools/                                    # 核心工程工具链
│   ├── dat_tool.py                           # .dat 二进制数据库解析与动态重打包核心库
│   ├── build_patch.py                        # 补丁总编译器 (生成 47 个 .dat 数据库)
│   ├── build_font_patch.py                   # 字库补丁编译器 (生成 misc_1_00.dat)
│   ├── build_fairy_patch.py                  # UI 贴图封包编译器 (修复 P0-4 主索引绝对偏移)
│   ├── apply_control_patch.py                # 桌面图标与 NACP 简体标题打包工具
│   ├── validate_batch.py                     # 全自动化质检门禁 (标签、字库覆盖、禁词审查)
│   ├── batch_status.py                       # 批次翻译进度查看器
│   ├── extract_batches.py                    # 原始数据批次切分工具
│   └── scan_calibration_targets.py           # 代词神怪、助词与角色口癖扫描器
├── workspace/                                # 汉化核心源数据
│   ├── batches/                              # 全量 289 个 JSON 文本批次 (55,931 行对照文本)
│   ├── font_codepoints.json                  # 当前字库 Unicode 码位白名单 (46,946 码位)
│   ├── glossary.json                         # 角色人设档案、禁词映射表、标点规范对照表
│   └── manifest.json                         # 289 个批次的字段与文件索引清单
├── PROJECT_HANDOVER.md                       # 项目全景接手指南 (Master Handover Document)
├── README.md                                 # 仓库中文主说明文档
└── README_EN.md                              # 仓库英文主说明文档
```

---

## 📚 详细文档导航 (Documentation Hub)

更详尽的开发与逆向资料请参阅各专项文档：
- 👉 [**PROJECT_HANDOVER.md (项目全景接手与维护指南)**](PROJECT_HANDOVER.md) —— 本项目最高优先级 master 文档，包含完整历史变更、架构与全景技术细节。
- 👉 [**docs/ARCHITECTURE.md (底层技术架构与逆向工程手册)**](docs/ARCHITECTURE.md) —— 深入剖析 FAFULLFS 容器、FAD 描述符、NVN Tegra Block Linear Swizzle 及 UV 路由机制。
- 👉 [**docs/LOCALIZATION_GUIDE.md (本地化规范与质量红线指南)**](docs/LOCALIZATION_GUIDE.md) —— 详述代词神魔判定、语气词脱繁入简、禁词列表与角色人设口癖。
- 👉 [**docs/BUILD_GUIDE.md (工程编译与实机部署指南)**](docs/BUILD_GUIDE.md) —— 包含从环境配置、编译流水线到实机与模拟器部署的完整步骤。
- 👉 [**docs/CRASH_AUDIT.md (实机崩溃审查与排查报告)**](docs/CRASH_AUDIT.md) —— 详细记录攻克实机报错、P0-4 索引越界与显存对齐的逆向攻坚过程。
- 👉 [**docs/NON_MAINLAND_AUDIT.md (非大陆用法排查报告)**](docs/NON_MAINLAND_AUDIT.md) —— 记录对 55,931 行文本进行港台用语与句式清洗的审计成果。

---

## ❓ 常见问题与解答 (FAQ)

**Q: 为什么小地图上的地点文字在文本数据库中搜不到？**  
A: 这 18 个地名是烘焙在小地图大贴图切片中的图片素材。本项目通过修改 `texture.dat` 中的贴图切片 UV 寻址，将其直接重定向至官方 PC 版的简体中文图元流，**补丁体积 0 字节膨胀**即可生效！

**Q: 为什么修改了 `string.dat`，主界面的“(X) 版权标示”文字还是繁体？**  
A: 该文字是 UI 纹理切片 `anm_0010_13`，必须在 `framework_texture.dat` 与 `texture.dat` 中建立 UV 重定向才能生效。本项目编译出的数据库已自动包含此项重定向。

**Q: 将补丁放入 Switch 后，游戏提示“程序发生错误”退出怎么办？**  
A: 本项目的 47 个数据库与字库归档 `misc_1_00.dat` 已经受严苛验证，100% 稳定运行。若自行编译了 `fairy_1_00.dat` 并发生报错，请确保使用最新的 `tools/build_fairy_patch.py`（该版本已修复 P0-4 主索引表绝对物理偏移），或直接从 Release 下载官方验证版本。

---

## ⚖️ 免责声明与版权信息 (Disclaimer & License)

1. 本项目为民间粉丝非商业性本地化与逆向技术研究项目，仅供学习、交流与实机体验使用。
2. 游戏《ほの暮しの庭 / Village in the Shade / 靜謐田園》的原版程序、图像、音频、文本及相关知识产权归原开发商及发行商 **Clouded Leopard Entertainment Inc.** 所有。
3. 请在支持正版游戏的前提下体验本项目。严禁将本项目任何代码、数据或补丁产物用于商业销售或营利行为。
4. 本项目开源工具链代码以 **MIT License** 授权使用；中文字体来源于开源字库项目 [LXGW WenKai (霞鹜文楷)](https://github.com/lxgw/LxgwWenKai)（SIL Open Font License 1.1）。
