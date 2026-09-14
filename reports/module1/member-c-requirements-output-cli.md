# 模块一 成员C 需求分析——输出与命令行域

被测版本：python-qrcode v8.2（commit `3704f57`）。本文件由成员C人工编写，
对应独立测试域：**输出与命令行**。断言对象为最终图像、文本、文件或 CLI 输出。

## 1. 被测源码范围

| 源码文件 | 职责 |
|---|---|
| `qrcode/image/base.py` | `BaseImage` 基类：几何属性 `pixel_size/width/border/box_size`、`pixel_box`、`check_kind`、`is_eye`、`save` 抽象契约 |
| `qrcode/image/pil.py` | `PilImage`：基于 PIL 的 PNG 输出，默认格式 PNG，支持黑白/透明/彩色 |
| `qrcode/image/pure.py` | `PyPNGImage`：基于 pypng 的纯 Python PNG 输出，1 位灰度 |
| `qrcode/image/svg.py` | `SvgImage`/`SvgFragmentImage`/`SvgPathImage`/`SvgFillImage`：SVG 输出 |
| `qrcode/compat/etree.py` | ET 后端选择（优先 lxml，回退标准库 ElementTree） |
| `qrcode/compat/png.py` | PngWriter 后端选择（pypng） |
| `qrcode/console_scripts.py` | `qr` CLI 入口 `main()`：`--factory`、`--output`、`--ascii`、`--error-correction`、`--optimize`、`--factory-drawer` |
| `qrcode/main.py`（输出方法） | `print_tty()`、`print_ascii()`、`make_image()` |

不负责范围（属其他成员或不在模块一范围内）：编码/纠错中间值（A）、
QRCode 对象内部状态/掩码选择/矩阵结果（B）、`image/styledpil.py`、`image/styles/*`、`release.py`。

## 2. 功能点与需求依据

### 2.1 几何属性（BaseImage）
- `pixel_size = (width + border*2) * box_size`，其中 `width = modules_count = version*4+17`。
- `pixel_box(row, col)` 返回 `((x,y),(x+box_size-1, y+box_size-1))`，坐标不得越界。
- 验证点：默认参数（version=1, box_size=10, border=4）下 `pixel_size=290`。

### 2.2 PNG 输出（PilImage / PyPNGImage）
- **PilImage 默认黑白**：模式 `"1"`，`fill_color=0`，背景 `255`。
- **PilImage 透明背景**：`back_color="transparent"` → 模式 `RGBA`，静区 alpha=0。
- **PilImage 自定义彩色**：非黑/白配色 → 模式 `RGB`。
- **PyPNGImage**：1 位灰度 PNG，`allowed_kinds=("PNG",)`；`save` 支持流与文件路径两条分支。
- **合法 PNG 契约**：魔数 `\x89PNG\r\n\x1a\n`，尺寸 = `pixel_size × pixel_size`。
- **跨后端一致性**：同参数下 PIL 与 PyPNG 静区/定位眼像素一致。
- **kind 校验契约**：基类 `check_kind` 对 `allowed_kinds` 之外的类型必须拒绝（抛 `ValueError`）且不写入字节。

### 2.3 SVG 输出
- `SvgImage`：独立 SVG 文档，根元素 `<svg xmlns="http://www.w3.org/2000/svg">`，
  `width/height` = `pixel_size` 对应的 mm 单位（box_size 10 = 1mm）。
- `SvgFillImage`：在 `SvgImage` 基础上插入白色背景 `<rect>`。
- `SvgPathImage`：`needs_processing=True`，`process()` 将所有模块合并为单一 `<path>` 元素，
  `d` 属性非空，`fill="#000000"`。

### 2.4 ASCII / TTY 输出（main.py）
- `print_ascii(out, tty, invert)`：
  - `tty=True` 且流非 tty → 抛 `OSError`。
  - 按每 2 行合并为 1 行输出，行数 = `ceil(modcount/2)`（border=0 时）。
  - `invert=True` 反转字符集（黑↔白）。
  - border=0 时每行可见字符数 = `modcount`。
- `print_tty(out)`：
  - 流非 tty → 抛 `OSError`。
  - 静区（border）宽度必须遵循 `self.border`，**与 `print_ascii` 一致**，
    行可见宽度 = `modcount*2 + border*4`。
  - QR 规范要求静区 ≥ 4 模块；`print_tty` 不得将静区写死为 1 模块。

### 2.5 CLI 入口（console_scripts.main）
- `--output FILE`：将图像写入指定文件（二进制）。
- `--factory NAME`：选择图像后端（pil/png/svg/svg-fragment/svg-path）。
- `--ascii`：以 ASCII 输出到标准输出，行数 = `range(-border, modcount+border, 2)` 的长度。
- 未指定 `--factory` 且 stdout 为 tty 或 `--ascii` 时走 ASCII 分支。

## 3. 有效输入 / 异常输入 / 预期结果

| 输入类别 | 示例 | 预期结果 |
|---|---|---|
| 合法几何 | version=1, box_size=10, border=4 | pixel_size=290 |
| 边界几何 | box_size=1, border=0 | 图像 21×21，pixel_box 端点闭合 |
| 合法 PNG 流 | save(BytesIO) | 魔数正确、可重开、尺寸一致 |
| 非法 kind | PyPNG.save(kind="JPEG") | ValueError，流为空 |
| 合法 SVG | SvgImage.save | 根 svg 元素、命名空间、mm 尺寸 |
| 非法 tty | print_ascii(tty=True) 于非 tty | OSError |
| CLI --output | main(["--output",f,"data"]) | 合法 PNG 文件 |
| CLI --ascii | main(["--ascii","data"]) | ASCII 输出，15 行（border=4） |
