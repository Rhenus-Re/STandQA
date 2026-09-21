# -*- coding: utf-8 -*-
"""模块二 · 成员 C（输出与命令行）AI 生成并经人工审核的测试。

用例编号 TC-C-AI-01 ~ TC-C-AI-08，与模块一 TC-C-001~012 不重复，
分三批提交（图像输出、CLI 与静区、tty 与缺陷回归）。
每条用例的审核结论见 ai_records/AI-2026-09-18-成员C-输出与命令行AI测-01.md。
缺陷 M2-C-01（CLI --factory 导入失败未友好处理）由 TC-C-AI-08 定位并回归。

设计方法分布：
  - 等价类：TC-C-AI-01 / 05 / 08
  - 边界值：TC-C-AI-02 / 06
  - 场景法：TC-C-AI-03 / 04 / 07
"""
import io
import math
import re

import png
import pytest
from PIL import Image

import qrcode
from qrcode import console_scripts
from qrcode.compat.etree import ET
from qrcode.image.pil import PilImage
from qrcode.image.svg import SvgFragmentImage, SvgPathImage

# 与模块一不同的短数据，保证输出确定可断言。
DATA = "M2-AI"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8\xff\xe0"
_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _make_qr(image_factory, box_size=10, border=4, **image_kwargs):
    qr = qrcode.QRCode(version=1, box_size=box_size, border=border)
    qr.add_data(DATA)
    return qr.make_image(image_factory=image_factory, **image_kwargs)


def _cli(monkeypatch, capsys, args):
    """在源码运行环境下执行 CLI main()（模拟包版本号为 8.2）。"""
    monkeypatch.setattr(console_scripts.metadata, "version", lambda name: "8.2")
    console_scripts.main(args)


class _FakeTty:
    """可写、可 isatty() 的假终端。"""

    def __init__(self):
        self.buf = []

    def write(self, s):
        self.buf.append(s)

    def flush(self):
        pass

    def isatty(self):
        return True


# ---------------------------------------------------------------------------
# TC-C-AI-01 PilImage.save 格式参数（等价类）
# ---------------------------------------------------------------------------
def test_tc_c_ai_01_pil_save_format_kind_equivalence(tmp_path):
    """TC-C-AI-01（等价类）：PilImage.save 的 kind 参数直接映射为 PIL 的
    format——默认产出 PNG；显式 kind="JPEG" 产出真 JPEG（与 PyPNGImage 的
    kind 白名单校验不同，PilImage 不经 check_kind，此分支模块一未覆盖）。"""
    # 默认：PNG
    buf = io.BytesIO()
    _make_qr(PilImage).save(buf)
    assert buf.getvalue()[:8] == PNG_SIGNATURE

    # kind="JPEG"：产出 JPEG 且可被 PIL 重新识别
    jbuf = io.BytesIO()
    _make_qr(PilImage).save(jbuf, kind="JPEG")
    data = jbuf.getvalue()
    assert data[:4] == JPEG_SIGNATURE
    reopened = Image.open(io.BytesIO(data))
    reopened.load()
    assert reopened.format == "JPEG"

    # 文件路径分支同样生效
    path = tmp_path / "c-ai-01.jpg"
    _make_qr(PilImage).save(str(path), kind="JPEG")
    with open(path, "rb") as f:
        assert f.read(4) == JPEG_SIGNATURE


# ---------------------------------------------------------------------------
# TC-C-AI-02 SVG 单位换算（边界值）
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("box_size,expected_mm", [(1, "2.9mm"), (3, "8.7mm"), (5, "14.5mm")])
def test_tc_c_ai_02_svg_unit_conversion_boundary(box_size, expected_mm):
    """TC-C-AI-02（边界值）：SVG width/height = pixel_size/10 的 mm 换算，
    box_size=1（最小常用值）到 5（非默认值）均成立；SvgPathImage 的 viewBox
    数值等于同一换算的无单位结果。模块一 TC-C-007 仅覆盖默认 box_size=10。"""
    img = _make_qr(SvgPathImage, box_size=box_size, border=4)
    buf = io.BytesIO()
    img.save(buf)
    root = ET.fromstring(buf.getvalue())
    assert root.get("width") == expected_mm
    assert root.get("height") == expected_mm

    expected_unit = img.pixel_size / 10
    assert root.get("viewBox") == f"0 0 {expected_unit} {expected_unit}"


# ---------------------------------------------------------------------------
# TC-C-AI-03 SvgFragmentImage 片段输出（场景法）
# ---------------------------------------------------------------------------
def test_tc_c_ai_03_svg_fragment_scenario():
    """TC-C-AI-03（场景法）：SvgFragmentImage 产出可嵌入的 SVG 文档片段——
    不写 XML 声明（区别于 SvgImage/SvgPathImage 的独立文档），根元素为
    带命名空间的 svg、声明 version=1.1 与 mm 尺寸。该后端模块一未覆盖。"""
    img = _make_qr(SvgFragmentImage, box_size=10, border=4)
    buf = io.BytesIO()
    img.save(buf)
    out = buf.getvalue()

    assert not out.startswith(b"<?xml"), "片段不应包含 XML 声明"
    root = ET.fromstring(out)
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert root.get("version") == "1.1"
    assert root.get("width") == "29mm"
    assert root.get("height") == "29mm"
