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


# ---------------------------------------------------------------------------
# TC-C-AI-04 CLI 全后端矩阵（场景法）
# ---------------------------------------------------------------------------
def test_tc_c_ai_04_cli_all_factories_scenario(tmp_path, monkeypatch, capsys):
    """TC-C-AI-04（场景法）：qr CLI 的 --factory 内置后端逐一产出生成物——
    png（PyPNG 合法 PNG）、svg-fragment（无声明片段）、svg-path（独立 SVG 文档
    且含单一 path）。模块一 TC-C-012 仅覆盖默认 pil 与 svg 两个后端。"""
    # png 后端：PyPNG 输出合法 1 位灰度 PNG
    png_path = tmp_path / "c-ai-04.png"
    _cli(monkeypatch, capsys, ["--factory", "png", "--output", str(png_path), DATA])
    reader = png.Reader(filename=str(png_path))
    width, height, _, info = reader.read()
    assert (width, height) == (290, 290)
    assert info["greyscale"] and info["bitdepth"] == 1

    # svg-fragment 后端：片段无 XML 声明
    frag_path = tmp_path / "c-ai-04-fragment.svg"
    _cli(monkeypatch, capsys, ["--factory", "svg-fragment", "--output", str(frag_path), DATA])
    frag = frag_path.read_bytes()
    assert not frag.startswith(b"<?xml")
    assert ET.fromstring(frag).tag == "{http://www.w3.org/2000/svg}svg"

    # svg-path 后端：独立文档、单一 path 元素
    path_path = tmp_path / "c-ai-04-path.svg"
    _cli(monkeypatch, capsys, ["--factory", "svg-path", "--output", str(path_path), DATA])
    raw = path_path.read_bytes()
    assert raw.startswith(b"<?xml")
    paths = [e for e in ET.fromstring(raw).iter() if e.tag.endswith("path")]
    assert len(paths) == 1 and paths[0].get("fill") == "#000000"


# ---------------------------------------------------------------------------
# TC-C-AI-05 CLI --error-correction 值域（等价类）
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("level", ["L", "M", "Q", "H"])
def test_tc_c_ai_05_cli_error_correction_levels(level, tmp_path, monkeypatch, capsys):
    """TC-C-AI-05（等价类）：CLI --error-correction 的 L/M/Q/H 全部合法级别
    均产出可被 PIL 重开的合法 PNG；非法级别走 optparse choice 校验，
    以 SystemExit 2 友好退出（作为 CLI 参数校验的对照基线，模块一未覆盖）。"""
    out = tmp_path / f"c-ai-05-{level}.png"
    _cli(monkeypatch, capsys, ["--error-correction", level, "--output", str(out), DATA])
    with Image.open(out) as im:
        assert im.format == "PNG"
        assert im.size == (290, 290)


def test_tc_c_ai_05_cli_error_correction_invalid(tmp_path, monkeypatch, capsys):
    """TC-C-AI-05 补充：非法纠错级别 X 的 CLI 友好错误（SystemExit 2）。"""
    with pytest.raises(SystemExit) as exc:
        _cli(monkeypatch, capsys, ["--error-correction", "X", "--output", str(tmp_path / "x.png"), DATA])
    assert exc.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# TC-C-AI-06 print_ascii 静区奇偶边界（边界值）
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("border,expected_lines", [(1, 12), (2, 13), (3, 14)])
def test_tc_c_ai_06_print_ascii_quiet_zone_parity(border, expected_lines):
    """TC-C-AI-06（边界值）：print_ascii 行数 = ceil((modcount+2*border)/2)、
    每行可见字符数 = modcount+2*border，奇偶静区（border=1/2/3）均成立。
    模块一 TC-C-009 仅覆盖 border=0、TC-C-012 仅覆盖默认 border=4。"""
    qr = qrcode.QRCode(version=1, box_size=1, border=border)
    qr.add_data(DATA)
    qr.make()

    out = io.StringIO()
    qr.print_ascii(out=out)
    lines = out.getvalue().splitlines()

    assert len(lines) == expected_lines == math.ceil((qr.modules_count + 2 * border) / 2)
    assert all(len(l) == qr.modules_count + 2 * border for l in lines)


# ---------------------------------------------------------------------------
# TC-C-AI-07 print_ascii tty ANSI 契约（场景法）
# ---------------------------------------------------------------------------
def test_tc_c_ai_07_print_ascii_tty_ansi_scenario():
    """TC-C-AI-07（场景法）：print_ascii(tty=True) 在真实可写终端上输出
    ANSI 着色行——强制 invert（静区渲染为实心块）；每行含前景码 38;5;255
    并以 \x1b[0m 结束；背景码 48;5;232 仅出现在非末行（末行 r=modcount+border-1
    时不写背景码，为源码显式分支）；可见行宽与普通输出一致。模块一仅覆盖
    tty 守卫异常（TC-C-010）与 print_tty 宽度（TC-C-011），未断言 ANSI 内容。"""
    qr = qrcode.QRCode(version=1, box_size=1, border=4)
    qr.add_data(DATA)
    qr.make()

    ft = _FakeTty()
    qr.print_ascii(out=ft, tty=True)
    tty_out = "".join(ft.buf)
    tty_lines = tty_out.splitlines()

    plain = io.StringIO()
    qr.print_ascii(out=plain)
    plain_lines = plain.getvalue().splitlines()

    # 行数与可见宽度与普通输出一致
    assert len(tty_lines) == len(plain_lines) == 15
    visible = [_ANSI.sub("", l) for l in tty_lines]
    assert all(len(v) == qr.modules_count + 2 * qr.border for v in visible)

    # tty 强制 invert：静区渲染为实心块，与普通输出的静区字符不同
    assert visible[0][0] != plain_lines[0][0]

    for i, line in enumerate(tty_lines):
        assert line.endswith("\x1b[0m"), f"第 {i} 行缺少 ANSI 重置码"
        assert "\x1b[38;5;255m" in line, f"第 {i} 行缺少前景色码"
        if i < len(tty_lines) - 1:
            assert "\x1b[48;5;232m" in line, f"第 {i} 行缺少背景色码"
        else:
            assert "\x1b[48;5;232m" not in line, "末行不应包含背景色码"


# ---------------------------------------------------------------------------
# TC-C-AI-08 CLI --factory 无效值处理（等价类，缺陷 M2-C-01 回归）
# ---------------------------------------------------------------------------
def test_tc_c_ai_08_cli_factory_invalid_handling(tmp_path, monkeypatch, capsys):
    """TC-C-AI-08（等价类，M2-C-01 回归）：--factory 无效输入必须统一走
    optparse 友好错误（SystemExit 2 + 说明信息），与 --error-correction 的
    choice 校验行为一致。

    修复前：合法快捷键正常；无点非法值友好退出；但带点非法路径抛出未捕获的
    ModuleNotFoundError（pil.PilImage）或 AttributeError（qrcode.image.pil.NoSuchImage）
    原始 traceback。修复后三类输入均为 SystemExit 2。
    """
    # 合法快捷键：正常生成（默认 pil 后端）
    ok_path = tmp_path / "c-ai-08-ok.png"
    _cli(monkeypatch, capsys, ["--factory", "pil", "--output", str(ok_path), DATA])
    with Image.open(ok_path) as im:
        assert im.format == "PNG"

    # 无点非法值：not a full python path
    with pytest.raises(SystemExit) as exc:
        _cli(monkeypatch, capsys, ["--factory", "foo", DATA])
    assert exc.value.code == 2
    assert "not a full python path" in capsys.readouterr().err

    # 带点非法模块：ModuleNotFoundError 场景（修复前为原始 traceback）
    with pytest.raises(SystemExit) as exc:
        _cli(monkeypatch, capsys, ["--factory", "pil.PilImage", DATA])
    assert exc.value.code == 2
    assert "Could not import" in capsys.readouterr().err

    # 带点非法类名：AttributeError 场景（修复前为原始 traceback）
    with pytest.raises(SystemExit) as exc:
        _cli(monkeypatch, capsys, ["--factory", "qrcode.image.pil.NoSuchImage", DATA])
    assert exc.value.code == 2
    assert "Could not import" in capsys.readouterr().err
