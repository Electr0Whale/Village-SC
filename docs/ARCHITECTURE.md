# 《静谧田园 (ほの暮しの庭)》底层技术架构与逆向工程手册
# Technical Architecture & Reverse Engineering Manual

本文档记录了《静谧田园 / ほの暮しの庭 / Village in the Shade》（Nintendo Switch 版，TitleID `01001BA027DD8000`，v1.2.0）的底层文件架构、二进制数据排布、逆向工程结论与补丁加载机制。

---

## 目录
1. [二进制数据库架构 (`romfs/data/database/*.dat`)](#1-二进制数据库架构)
2. [字号动态重平衡机制 (`font.dat`)](#2-字号动态重平衡机制)
3. [字库归档容器架构 (`misc_1_00.dat` & FAFULLFS)](#3-字库归档容器架构)
4. [贴图图集封包与 FAD 描述符流 (`fairy_1_00.dat`)](#4-贴图图集封包与-fad-描述符流)
5. [Tegra Block Linear 纹理重编码与 Swizzling](#5-tegra-block-linear-纹理重编码与-swizzling)
6. [零封包膨胀的贴图 UV 重定向机制](#6-零封包膨胀的贴图-uv-重定向机制)
7. [控制元数据与桌面图标架构 (NACP & Icons)](#7-控制元数据与桌面图标架构)

---

## 1. 二进制数据库架构

游戏运行时的数据驱动层由 189 个二进制 `.dat` 文件构成，其中承载本地化文本与界面配置的数据库共有 **47 个**。

### 1.1 基础表物理布局
数据库文件采用连续流布局：
```
[Header: Record Count (uint32)]
[Records Array: Count * Record Size]
  └── 固定字段 / 槽位结构 (MultiLangString 等)
[String Pool / Binary Payload]
  └── UTF-8 变长以 \x00 结尾的字符串连续存放区
```

### 1.2 7 槽位多语言结构 (`MultiLangString`)
游戏中的常规文本记录采用 56 字节的 `MultiLangString` 槽位描述结构（包含 7 个 8 字节指针）：
| 槽位索引 | 语言代号 | 语言名称 | 本项目处理策略 |
| :---: | :---: | :---: | :--- |
| `0` | `ja` | 日语原文 | **黄金基准 (Ground Truth)**，质检门禁的所有控制标签均严格与此槽位比对 |
| `1` | `en` | 英语 (若有) | 参照对照 |
| `2` | `fr` | 法语 (预留) | 保持原版 |
| `3` | `de` | 德语 (预留) | 保持原版 |
| `4` | `tc` | 繁体中文 | **主要注入槽位**：原位替换为中国大陆规范现代简体中文 (`sc`) |
| `5` | `ko` | 韩语 (若有) | 保持原版 |
| `6` | `sc` | 预留简中 | 原版多为空串；本工程规范化保持原版空指针，避免实机引擎内存越界 |

### 1.3 多行文本表 (`multiLineText.dat`)
村落布告栏、钟楼神话、长篇告示等长篇文本采用非固定步长的特殊记录结构：
- 头结构：`(unk1: uint32, unk2: uint32, line_count: uint32, offsets: uint32[line_count])`；
- 每个 offset 指向该记录局部的行文本起始位置；
- 本项目在 `tools/dat_tool.py` 中实现了对多行表动态计算变长行索引与全局字符串池重构的完整无损编解码器。

---

## 2. 字号动态重平衡机制

### 2.1 掌机字号过小痛点
Switch 掌机模式分辨率为 1280×720，相对于 1080p 底座模式存在 `0.667x` 线性下采样。原版移植时，官方将中文对话字体由日文原版的 32px 强制压缩至 26px，导致在 720p 掌机屏幕上实际渲染高度不足 17px，阅读极其费力。

### 2.2 引擎自动排版缩放机制 (Auto-Fit)
逆向分析发现，游戏引擎底层存在 `枠内に収めるための拡縮処理`（超长文本水平自适应压缩算法）。当文本渲染宽度超过对话框视口时，引擎会自动缩放字符字偶间距与 X 轴比例，而不会产生文本破框或越界。

### 2.3 `font.dat` 重平衡方案
通过修改 `font.dat` 对应语言槽位（TC 槽 `0x228`、SC 槽 `0x330`）的宽高配置，实现全局字号无损重平衡：
- `FONT_ID_GAME` (主菜单/通用UI)：由 26px 提升至 **32px** (面积提升 51%)；
- `FONT_ID_GAME_TALK` (主剧情对话)：由 26px 恢复至 **32px** (1:1 完美契合日文原版)；
- `FONT_ID_GAME_SMALL_TEXT` (道具/书籍详述)：由 24px 优化至 **26px**。

---

## 3. 字库归档容器架构

字库及部分鱼类图标被封装在 `romfs/data/misc_1_00.dat` 归档中，该文件采用 `FAFULLFS` 虚拟文件系统格式。

### 3.1 `FAFULLFS` 标头结构 (`0x00 - 0x20`)
```c
struct FAFULLFS_Header {
    char     magic[8];       // "FAFULLFS"
    uint32_t file_count;     // 文件总数 (15)
    uint32_t unknown;        // 保留字段
    uint64_t str_table_off;  // 路径字符串表绝对偏移
    uint64_t str_table_len;  // 路径字符串表长度
    uint64_t toc_offset;     // 文件索引表 (TOC) 绝对偏移
};
```

### 3.2 TOC 索引表项结构 (每项 48 字节)
```c
struct FAFULLFS_Entry {
    uint64_t name_hash;      // 路径 FNV / 专有哈希值
    uint64_t str_offset;     // 在字符串表中的相对偏移
    uint64_t flags;          // 文件属性标记
    uint64_t file_size;      // 文件实际字节长度
    uint64_t file_offset;    // 文件负载在归档中的绝对偏移 (0x200 字节对齐)
    uint64_t timestamp;      // 时间戳
};
```

### 3.3 字型注入与霞鹜文楷等宽
本项目在重构 `misc_1_00.dat` 时，将原版的繁体圆体全面升级为 **霞鹜文楷等宽 (LXGW WenKai Mono v1.530)**：
- 替换目标：`data/misc/resourcehanroundedtc-regular.ttf`、`data/misc/resourcehanroundedtc-medium.ttf`、`data/misc/lxgwwenkaimonotc-bold.ttf`；
- 通过 `fontTools` 动态注入原版 TTF 的 `name` 表（Family Name、Subfamily Name、PostScript Name），确保引擎字库加载器识别为原生字体；
- 字符集覆盖超 46,946 码位，彻底告别缺字豆腐块（□）。

---

## 4. 贴图图集封包与 FAD 描述符流

### 4.1 `fairy_1_00.dat` 架构
- 文件体积：约 1.15 GB；
- 格式：`FAFULLFS`；
- 包含 9 个子文件，本地化贴图集中在最后一个子文件 `data/fairy/resident_lang_tc.fad` 中；
- 前 8 个系统文件（`resident.fad`、`resident_2.fad`、`anmlayer.dat` 等）保持 100% 二进制位无修改。

### 4.2 FAD 贴图流结构 (`0x33FB60` 起)
`resident_lang_tc.fad` 内部按顺序串联了 411 个贴图数据块，每个数据块的物理排布如下：
```
[64-Byte 前导描述符 (Descriptor)]
[128-Byte NMPLTEX1 标头]
[20-Byte YKCMP_V1 容器标头]
[LZ4 压缩纹理负载]
```

### 4.3 P0 级致命暗坑攻坚与定性

#### P0-1: 压缩长度少算 20 字节
- **原版规范**：Switch 引擎中，`YKCMP_V1` 头部的 `comp_sz` 与 `NMPLTEX1` 头部的 `ints[12]` 定义均为 **20 字节 YK 头部 + LZ4 压缩负载** 的**总字节数**。
- **修复**：`comp_sz = 20 + len(lz4_payload)`。Switch 引擎执行 `LZ4_decompress_safe(src+20, comp_sz-20)` 时能够 100% 精确命中有效载荷，彻底解决加载后程序报错崩溃。

#### P0-2: 描述符格式升级为标准 BC3
- 原版 411 张贴图中，有 385 张为 Switch 专有高压格式 `0x0B`。
- 本项目在全量路线 B 中，重构 64 字节前导描述符：将 `q6` 低 32 位升级为标准 BC3 格式标记 `0x07050080`，`ints[5]` 写入 `0x800006`，解压尺寸严格同步为 $w \times h$ 字节，使 GPU 正确按 BC3 纹理格式分配与绑定显存。

#### P0-3: 动态 Tegra Swizzle 块高适配
- `NMPLTEX1` 头部 `ints[14]` 低字节（bit 0~7）存储了该贴图在 Tegra NVN 硬件中的块高 log2 参数（取值 0~4）。
- 本项目动态读取原版 `ints[14] & 0xFF` 并应用至 Swizzling 编码器中，彻底杜绝画面撕裂和花屏。

#### P0-4: FAD 主索引查找表 (Master Texture Table) 偏移脱节
- **暗坑所在**：在 `resident_lang_tc.fad` 的 `0xd00` 至 `0x4060` 区域，存在一个拥有 411 项（每项 32 字节 `<8I`）的**主贴图索引查找表**！
- 每项的第 0 个 DWORD 记录该贴图在 FAD 中的**绝对物理字节偏移**；第 6 个 DWORD 记录下一张贴图的**步长 `step`**。
- **修复**：重打包时逐项重算并回写所有 411 项的真实最新绝对物理偏移与步长，彻底杜绝第一帧未映射内存访问死锁。

---

## 5. Tegra Block Linear 纹理重编码与 Swizzling

Nintendo Switch 搭载 NVIDIA Tegra X1 芯片，其 NVN 图形驱动要求 2D 纹理在显存中按照 **Block Linear (GOB - Group of Blocks)** 进行空间排布，而非普通的线性行排列（Pitch Linear）。

1. **GOB 基本单元**：每个 GOB 大小为 64 字节宽 × 8 行高（共 512 字节）；
2. **Block Height 参数**：`block_height_log2`（0~4），对应 1, 2, 4, 8, 16 个垂直堆叠的 GOB；
3. **重编码流水线**：
   - 提取 PC 官方高清 DDS/PNG 纹理；
   - 编码为 BC3 (DXT5) 块压缩像素流；
   - 调用 Tegra Block Linear Swizzle 算法，按贴图专属的 `block_height_log2` 进行内存交织排列；
   - 注入 `YKCMP_V1` 容器并使用原生 LZ4 压缩。

---

## 6. 零封包膨胀的贴图 UV 重定向机制

### 6.1 挑战与突破
小地图上的 18 个地名（如“水车小屋”、“樟树诊所”）以及主菜单上的“(X) 版权标示”并非字库文本，而是烘焙在大图集中的贴图切片。原切片存放在 1.15 GB 的 `fairy_1_00.dat` 中。若强行替换图集，补丁体积将额外增加 1.15 GB。

### 6.2 贴图切片路由重定向
1. 逆向解析 `romfs/data/database/texture.dat` 与 `framework_texture.dat`；
2. 提取 PC 官方 1.2.0 版本中的简中矢量贴图图元索引（`map_9999_icon_0001` ~ `0003` 及 `anm_0010_13`）；
3. 直接在数据库中重写小地图地名切片的 UV 寻址与贴图 ID 引用，将其无缝重定向到官方简中图元；
4. **技术成果**：补丁体积 **0 字节膨胀**，实现小地图地名与版权标示 100% 官方正版矢量级简体中文呈现！

---

## 7. 控制元数据与桌面图标架构

Switch 系统的应用元数据存放在 Control NCA 的 `control.nacp` 中，桌面图标存放在 `icon_*.dat`（标准 JPEG 格式，256×256 分辨率）。

### 7.1 NACP 语言槽位布局
- 文件总长度：固定 `0x4000` 字节；
- 语言槽位：共 16 个槽位，每个槽位占用 `0x300` 字节（前 `0x200` 字节为游戏标题 UTF-8，后 `0x100` 字节为发行商 UTF-8）：
  - `Slot 13` (偏移 `0x2700 - 0x2A00`)：繁体中文；
  - `Slot 14` (偏移 `0x2A00 - 0x2D00`)：简体中文。

### 7.2 标题与发行商写入规范
本项目通过 `tools/apply_control_patch.py` 将 `Slot 13` 与 `Slot 14` 均规范写入：
- 游戏标题：`静谧田园`
- 发行商：`Clouded Leopard Entertainment Inc.`

### 7.3 Atmosphere 实机免改包动态挂载
在 Atmosphere 补丁根目录放置：
`output/atmosphere/contents/01001BA027DD8000/icon.jpg`
配合 Atmosphere 常用插件 `sys-tweak` 或 `sys-icon`，无需重打包 NCA 即可在 Switch 官方桌面完美呈现全新简体中文游戏图标！
