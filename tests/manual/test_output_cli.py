# -*- coding: utf-8 -*-
"""模块一 成员C 人工测试：输出与命令行域

被测源码（python-qrcode v8.2，commit ``3704f57``）：
  - qrcode/image/base.py        BaseImage 几何、pixel_box、check_kind、is_eye
  - qrcode/image/pil.py         PilImage（PNG）
  - qrcode/image/pure.py        PyPNGImage（PNG）
  - qrcode/image/svg.py         SvgImage / SvgFragmentImage / SvgPathImage / SvgFillImage
  - qrcode/compat/etree.py      ET 后端选择
  - qrcode/compat/png.py        PngWriter 后端选择
  - qrcode/console_scripts.py   qr CLI 入口
  - qrcode/main.py 的 print_tty() / print_ascii() / make_image()

设计方法分布：
  - 等价类：TC-C-001 / 004 / 006 / 007 / 010
  - 边界值：TC-C-002 / 009
  - 场景法：TC-C-003 / 005 / 008 / 011 / 012

所有用例均由成员C人工依据源码与图像/CLI 契约设计，未使用 AI 生成。
"""
import io
import math
import re
import warnings

import png
import pytest
from PIL import Image

import qrcode
from qrcode.compat.etree import ET
from qrcode.image.pil import PilImage
from qrcode.image.pure import PyPNGImage
from qrcode.image.svg import SvgFillImage, SvgImage, SvgPathImage

# 固定 version=1（21x21 模块）+ 短 ASCII 数据，保证输出确定可断言。
DATA = "M1-CLI"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _make_qr(image_factory, box_size=10, border=4, **image_kwargs):
    qr = qrcode.QRCode(version=1, box_size=box_size, border=border)
    qr.add_data(DATA)
    return qr.make_image(image_factory=image_factory, **image_kwargs)


class _FakeTty:
    """可写、可 isatty() 的假终端，用于测试 print_tty / print_ascii(tty=True)。"""

    def __init__(self):
        self.buf = []

    def write(self, s):
        self.buf.append(s)

    def flush(self):
        pass

    def isatty(self):
        return True


def _visible(s):
    """去掉 ANSI 颜色转义码，返回可见字符。"""
    return _ANSI.sub("", s)


# ---------------------------------------------------------------------------
# image/base.py + image/pil.py：PNG 输出
# ---------------------------------------------------------------------------
def test_tc_c_001_pil_geometry_and_mode_equivalence():
    """TC-C-001（等价类）：PilImage 默认黑白配色下几何属性与图像模式满足契约。

    pixel_size = (width + border*2) * box_size；默认黑/白使用二值模式 "1"，
    填充色归一化为 0、背景为 255。
    """
    img = _make_qr(PilImage, box_size=10, border=4)
    assert img.width == 21
    assert img.border == 4
    assert img.box_size == 10
    assert img.pixel_size == (21 + 4 * 2) * 10 == 290
    base = img.get_image()
    assert base.mode == "1"
    assert img.fill_color == 0
    assert base.size == (290, 290)


def test_tc_c_002_pil_min_params_pixels_boundary():
    """TC-C-002（边界值）：box_size=1、border=0 最小合法参数下，
    pixel_box 端点不越界；图像 21x21，左上定位眼首点为黑，
    水平定时图案（第 6 行）从第 8 列起奇偶交替。"""
    img = _make_qr(PilImage, box_size=1, border=0)
    assert img.pixel_size == 21
    assert img.pixel_box(0, 0) == ((0, 0), (0, 0))
    assert img.pixel_box(20, 20) == ((20, 20), (20, 20))

    base = img.get_image()
    assert base.size == (21, 21)
    assert base.getpixel((0, 0)) == 0  # 左上定位眼 (0,0) 为黑
    # 行 6 为水平定时图案：col>=8 起偶数列黑、奇数列白
    assert base.getpixel((8, 6)) == 0
    assert base.getpixel((9, 6)) == 255
    assert base.getpixel((10, 6)) == 0


def test_tc_c_003_pil_png_roundtrip_scenario(tmp_path):
    """TC-C-003（场景法）：QRCode.make_image → save 完整链路，
    输出为合法 PNG（魔数正确、可被 PIL 重新打开且尺寸一致），
    保存到文件路径后文件可被外部正常打开。"""
    img = _make_qr(PilImage)
    buf = io.BytesIO()
    img.save(buf)
    data = buf.getvalue()
    assert data[:8] == PNG_SIGNATURE
    reopened = Image.open(io.BytesIO(data))
    reopened.load()
    assert reopened.format == "PNG"
    assert reopened.size == (290, 290)

    path = tmp_path / "c003-roundtrip.png"
    _make_qr(PilImage).save(str(path))
    with Image.open(path) as from_file:
        assert from_file.format == "PNG"
        assert from_file.size == (290, 290)


def test_tc_c_004_pil_color_modes_equivalence():
    """TC-C-004（等价类）：PilImage 颜色模式三分支——
    默认黑/白→"1"；back_color="transparent"→RGBA（静区 alpha=0）；
    自定义不透明配色→RGB（静区为背景色、定位眼为填充色）。"""
    # 默认
    default = _make_qr(PilImage)
    assert default.get_image().mode == "1"

    # 透明背景
    transparent = _make_qr(PilImage, box_size=1, border=4, back_color="transparent")
    tbase = transparent.get_image()
    assert tbase.mode == "RGBA"
    assert tbase.getpixel((0, 0))[3] == 0  # 静区 alpha=0

    # 自定义彩色
    custom = _make_qr(
        PilImage, box_size=1, border=4, fill_color="red", back_color="yellow"
    )
    cbase = custom.get_image()
    assert cbase.mode == "RGB"
    assert cbase.getpixel((0, 0)) == (255, 255, 0)  # 黄色静区
    assert cbase.getpixel((4, 4)) == (255, 0, 0)  # 左上定位眼黑色模块→红


# ---------------------------------------------------------------------------
# image/pure.py：PyPNG 输出
# ---------------------------------------------------------------------------
def _decode_png(data):
    """用 pypng 解码，返回 (宽, 高, info, 行像素二维列表)。"""
    reader = png.Reader(file=io.BytesIO(data))
    width, height, rows, info = reader.read()
    return width, height, info, [list(row) for row in rows]


def test_tc_c_005_pypng_roundtrip_and_cross_backend_scenario():
    """TC-C-005（场景法）：PyPNG 后端端到端输出合法 1 位灰度 PNG，
    尺寸 290x290，静区为白(1)、定位眼为黑(0)，且与 PIL 后端像素一致。"""
    buf = io.BytesIO()
    _make_qr(PyPNGImage, box_size=10, border=4).save(buf)
    data = buf.getvalue()
    assert data[:8] == PNG_SIGNATURE

    width, height, info, rows = _decode_png(data)
    assert (width, height) == (290, 290)
    assert info["greyscale"] is True
    assert info["bitdepth"] == 1
    assert len(rows) == 290 and all(len(r) == 290 for r in rows)
    assert all(v == 1 for v in rows[0])  # 首行静区全白
    assert rows[40][40] == 0  # 左上定位眼区域（含静区偏移）为黑

    # 跨后端一致性：同参数下 PIL 静区/定位眼像素相同
    pil = _make_qr(PilImage, box_size=10, border=4).get_image()
    assert pil.getpixel((0, 0)) == 255
    assert pil.getpixel((40, 40)) == 0


def test_tc_c_006_pypng_kind_and_stream_equivalence(tmp_path):
    """TC-C-006（等价类）：PyPNGImage save 的流/路径两条分支均产出合法 PNG；
    非法 kind 在写入任何字节前即被 check_kind 拒绝（ValueError，流为空）。"""
    # 非法 kind 被拒绝且不写入字节
    bad = io.BytesIO()
    with pytest.raises(ValueError):
        _make_qr(PyPNGImage).save(bad, kind="JPEG")
    assert bad.getvalue() == b""

    # 默认值与 PNG 均正常
    ok = io.BytesIO()
    _make_qr(PyPNGImage).save(ok, kind="PNG")
    assert ok.getvalue()[:8] == PNG_SIGNATURE

    default = io.BytesIO()
    _make_qr(PyPNGImage).save(default)
    assert default.getvalue()[:8] == PNG_SIGNATURE

    # 路径分支
    path = tmp_path / "c006.png"
    _make_qr(PyPNGImage).save(str(path))
    with open(path, "rb") as f:
        assert f.read(8) == PNG_SIGNATURE


# ---------------------------------------------------------------------------
# image/svg.py：SVG 输出
# ---------------------------------------------------------------------------
def test_tc_c_007_svg_root_geometry_namespace_equivalence():
    """TC-C-007（等价类）：SvgImage 生成独立 SVG 文档，根元素为 svg、
    声明 SVG 命名空间，width/height = pixel_size 对应的 mm 单位；
    SvgFillImage 额外插入白色背景 rect。"""
    img = _make_qr(SvgImage, box_size=10, border=4)
    buf = io.BytesIO()
    img.save(buf)
    root = ET.fromstring(buf.getvalue())
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert root.get("width") == "29mm"  # pixel_size 290 / 10 = 29mm
    assert root.get("height") == "29mm"

    # SvgFillImage 含白色背景 rect
    fill_img = _make_qr(SvgFillImage, box_size=10, border=4)
    fbuf = io.BytesIO()
    fill_img.save(fbuf)
    froot = ET.fromstring(fbuf.getvalue())
    rects = [e for e in froot.iter() if e.tag.endswith("rect")]
    assert rects, "SvgFillImage 应至少含一个 rect"
    assert rects[0].get("fill") == "white"  # 背景矩形


def test_tc_c_008_svg_path_merge_scenario():
    """TC-C-008（场景法）：SvgPathImage 的 needs_processing=True，
    make_image 调用 process() 后将所有模块合并为单一 <path> 元素，
    其 d 属性非空、填充样式为 #000000。"""
    img = _make_qr(SvgPathImage, box_size=10, border=4)
    assert img.needs_processing is True
    assert img.path is not None  # process() 已执行

    buf = io.BytesIO()
    img.save(buf)
    root = ET.fromstring(buf.getvalue())
    paths = [e for e in root.iter() if e.tag.endswith("path")]
    assert len(paths) == 1
    assert len(paths[0].get("d", "")) > 0  # 路径数据非空
    assert paths[0].get("fill") == "#000000"


# ---------------------------------------------------------------------------
# main.py：ASCII / TTY 输出
# ---------------------------------------------------------------------------
def test_tc_c_009_print_ascii_invert_boundary():
    """TC-C-009（边界值）：border=0（最小合法静区）下 print_ascii 输出
    行数为 ceil(modcount/2)、每行可见字符数为 modcount；invert 反转字符集，
    invert 与非 invert 输出不同。"""
    qr = qrcode.QRCode(version=1, box_size=1, border=0)
    qr.add_data(DATA)
    qr.make()

    plain = io.StringIO()
    qr.print_ascii(out=plain)
    plain_out = plain.getvalue()
    lines = plain_out.splitlines()
    assert len(lines) == math.ceil(qr.modules_count / 2)  # 11
    assert all(len(l) == qr.modules_count for l in lines)  # 每行 21 字符

    inverted = io.StringIO()
    qr.print_ascii(out=inverted, invert=True)
    assert inverted.getvalue() != plain_out  # invert 反转字符集


def test_tc_c_010_tty_guard_equivalence():
    """TC-C-010（等价类）：print_ascii(tty=True) 与 print_tty() 在非 tty
    流上必须抛 OSError，不得继续输出。"""
    qr = qrcode.QRCode(version=1, box_size=1, border=4)
    qr.add_data(DATA)
    qr.make()

    # print_ascii(tty=True) 在非 tty 流抛 OSError
    with pytest.raises(OSError):
        qr.print_ascii(out=io.StringIO(), tty=True)

    # print_tty 在非 tty 流抛 OSError
    with pytest.raises(OSError):
        qr.print_tty(out=io.StringIO())


def test_tc_c_011_print_tty_respects_border_scenario():
    """TC-C-011（场景法，C-BUG-01 回归）：print_tty 输出的可见行宽必须
    等于 modcount*2 + border*4，即静区宽度遵循 self.border 而非硬编码为 1 模块。

    修复前 print_tty 把静区写死为每侧 1 模块（共 4 字符），忽略 self.border，
    导致默认 border=4 时行宽为 46 而非期望的 58。
    """
    qr = qrcode.QRCode(version=1, box_size=1, border=4)
    qr.add_data(DATA)
    qr.make()

    ft = _FakeTty()
    qr.print_tty(out=ft)
    visible = _visible("".join(ft.buf))
    lines = [l for l in visible.split("\n") if l != ""]

    expected_width = qr.modules_count * 2 + qr.border * 4  # 21*2 + 4*4 = 58
    assert expected_width == 58  # 自检
    assert lines, "print_tty 未产生任何输出行"
    for line in lines:
        assert len(line) == expected_width, (
            f"print_tty 行宽 {len(line)} != 期望 {expected_width}"
            f"（border={qr.border} 被忽略，修复前为 {len(line)}）"
        )


# ---------------------------------------------------------------------------
# console_scripts.py：CLI 入口
# ---------------------------------------------------------------------------
def test_tc_c_012_cli_end_to_end_scenario(tmp_path, monkeypatch):
    """TC-C-012（场景法）：qr CLI 端到端——
    --output 生成合法 PNG 文件；--factory svg --output 生成合法 SVG 文件；
    --ascii 将二维码以 ASCII 输出到标准输出。"""
    from qrcode import console_scripts

    # CLI 通过 importlib.metadata.version 获取版本号；源码运行时无包元数据，
    # 此处模拟为 8.2（与被测版本一致），不改变被测逻辑分支。
    monkeypatch.setattr(
        console_scripts.metadata, "version", lambda name: "8.2"
    )

    # 1) --output 生成 PNG
    png_path = tmp_path / "c012.png"
    console_scripts.main(["--output", str(png_path), DATA])
    with Image.open(png_path) as im:
        assert im.format == "PNG"
        assert im.size == (290, 290)

    # 2) --factory svg --output 生成 SVG
    svg_path = tmp_path / "c012.svg"
    console_scripts.main(["--factory", "svg", "--output", str(svg_path), DATA])
    root = ET.fromstring(svg_path.read_bytes())
    assert root.tag == "{http://www.w3.org/2000/svg}svg"

    # 3) --ascii 输出到 stdout
    captured = io.StringIO()

    class _FakeStdout:
        def __init__(self, text):
            self.buffer = io.BytesIO()
            self._text = text

        def write(self, s):
            self._text.write(s)
            return len(s)

        def flush(self):
            pass

        def fileno(self):
            return 1

    fake_stdout = _FakeStdout(captured)
    import sys

    monkeypatch.setattr(sys, "stdout", fake_stdout)
    # os.isatty 返回 False → 走 --ascii 分支（opts.ascii 为真）
    monkeypatch.setattr(console_scripts.os, "isatty", lambda fd: False)
    console_scripts.main(["--ascii", DATA])

    out = captured.getvalue()
    assert out, "CLI --ascii 未输出任何内容"
    assert len(out.splitlines()) == 15  # border=4: range(-4,25,2) → 15 行
    assert len(out.splitlines()[0]) == 29  # 21 + 4*2
