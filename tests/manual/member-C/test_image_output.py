# -*- coding: utf-8 -*-
"""模块一 成员C 人工测试：图像输出层 image/base.py、image/pil.py、image/pure.py。

用例编号        设计方法   需求依据/断言对象
TC-C-IMG-001    等价类     BaseImage 几何属性 pixel_size/width/border/box_size
TC-C-IMG-002    边界值     BaseImage.pixel_box 最小参数坐标
TC-C-IMG-003    等价类     BaseImage.check_kind 合法/默认/非法类型
TC-C-IMG-004    等价类     BaseImage.is_eye 三个定位眼区域
TC-C-IMG-005    等价类     PilImage 默认黑白输出模式（"1"）
TC-C-IMG-006    等价类     PilImage 透明背景（RGBA）
TC-C-IMG-007    等价类     PilImage 自定义彩色（RGB）
TC-C-IMG-008    场景法     PilImage 端到端 PNG 输出（流/文件）
TC-C-IMG-009    边界值     PilImage 像素级输出正确性（静区/定位眼/定时图案）
TC-C-IMG-010    场景法     PyPNGImage 端到端 PNG 输出与跨后端像素一致性
TC-C-IMG-011    场景法     PyPNGImage 路径保存后文件句柄必须关闭（C-BUG-01 回归）
TC-C-IMG-012    等价类     PyPNGImage 仅允许 PNG 输出（C-BUG-02 回归）

所有用例均由成员C人工依据源码与图像格式常识设计，未使用 AI 生成。
"""
import gc
import io
import os
import warnings

import png
import pytest
from PIL import Image

import qrcode
from qrcode.image.pil import PilImage
from qrcode.image.pure import PyPNGImage

# 固定 version=1（21x21 模块）+ 短 ASCII 数据，保证输出确定可断言。
DATA = "M1-IMG"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _make_qr(image_factory, box_size=10, border=4, **image_kwargs):
    qr = qrcode.QRCode(version=1, box_size=box_size, border=border)
    qr.add_data(DATA)
    return qr.make_image(image_factory=image_factory, **image_kwargs)


# ---------------------------------------------------------------------------
# image/base.py
# ---------------------------------------------------------------------------
def test_tc_c_img_001_base_geometry_equivalence():
    """TC-C-IMG-001（等价类）：两种图像后端的几何属性均满足
    pixel_size = (width + border*2) * box_size。"""
    pil_img = _make_qr(PilImage, box_size=10, border=4)
    png_img = _make_qr(PyPNGImage, box_size=10, border=4)
    for img in (pil_img, png_img):
        assert img.width == 21
        assert img.border == 4
        assert img.box_size == 10
        assert img.pixel_size == (21 + 4 * 2) * 10 == 290


def test_tc_c_img_002_pixel_box_min_boundary():
    """TC-C-IMG-002（边界值）：box_size=1、border=0 最小合法参数下，
    pixel_box 返回包含端点的像素矩形，且无越界坐标。"""
    img = _make_qr(PilImage, box_size=1, border=0)
    assert img.pixel_size == 21
    assert img.pixel_box(0, 0) == ((0, 0), (0, 0))
    assert img.pixel_box(20, 20) == ((20, 20), (20, 20))
    assert img.pixel_box(10, 5) == ((5, 10), (5, 10))


def test_tc_c_img_003_check_kind_equivalence():
    """TC-C-IMG-003（等价类）：check_kind 对默认值、允许值放行，
    对 allowed_kinds 之外的类型必须拒绝。"""
    img = _make_qr(PyPNGImage)
    assert img.check_kind(None) == "PNG"
    assert img.check_kind("PNG") == "PNG"
    with pytest.raises(ValueError):
        img.check_kind("JPEG")


def test_tc_c_img_004_is_eye_equivalence():
    """TC-C-IMG-004（等价类）：is_eye 仅对左上、右上、左下三个 7x7
    定位眼区域内的模块返回 True。"""
    img = _make_qr(PilImage)
    # 三个定位眼内部
    assert img.is_eye(0, 0) is True
    assert img.is_eye(6, 20) is True
    assert img.is_eye(20, 6) is True
    # 紧贴定位眼外侧、中央数据区均不属于眼
    assert img.is_eye(7, 7) is False
    assert img.is_eye(6, 7) is False
    assert img.is_eye(10, 10) is False


# ---------------------------------------------------------------------------
# image/pil.py
# ---------------------------------------------------------------------------
def test_tc_c_img_005_pil_default_mode_equivalence():
    """TC-C-IMG-005（等价类）：默认黑/白配色使用二值模式 "1"，
    填充色与背景色归一化为 0/255。"""
    img = _make_qr(PilImage)
    assert img.get_image().mode == "1"
    assert img.fill_color == 0
    assert img.get_image().size == (290, 290)


def test_tc_c_img_006_pil_transparent_equivalence():
    """TC-C-IMG-006（等价类）：back_color="transparent" 时输出 RGBA，
    静区背景像素 alpha 通道为 0（全透明）。"""
    img = _make_qr(PilImage, box_size=1, border=4, back_color="transparent")
    base = img.get_image()
    assert base.mode == "RGBA"
    assert base.getpixel((0, 0))[3] == 0


def test_tc_c_img_007_pil_custom_color_rgb_equivalence():
    """TC-C-IMG-007（等价类）：自定义不透明配色使用 RGB 模式，
    静区为背景色、定位眼位置为填充色。"""
    img = _make_qr(
        PilImage, box_size=1, border=4, fill_color="red", back_color="yellow"
    )
    base = img.get_image()
    assert base.mode == "RGB"
    assert base.getpixel((0, 0)) == (255, 255, 0)      # 黄色静区
    assert base.getpixel((4, 4)) == (255, 0, 0)        # 左上定位眼黑色模块→红


def test_tc_c_img_008_pil_png_roundtrip_scenario(tmp_path):
    """TC-C-IMG-008（场景法）：QRCode.make_image → save 完整链路，
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

    path = tmp_path / "pil-roundtrip.png"
    _make_qr(PilImage).save(str(path))
    with Image.open(path) as from_file:
        assert from_file.format == "PNG"
        assert from_file.size == (290, 290)


def test_tc_c_img_009_pil_pixels_boundary():
    """TC-C-IMG-009（边界值）：box_size=1、border=0 时直接校验像素：
    图像 21x21；左上角定位眼首点为黑；水平定时图案奇偶交替。"""
    img = _make_qr(PilImage, box_size=1, border=0)
    base = img.get_image()
    assert base.size == (21, 21)
    assert base.getpixel((0, 0)) == 0       # 左上定位眼 (0,0) 为黑
    # 行6为水平定时图案：col>=8 起，偶数列黑、奇数列白
    assert base.getpixel((8, 6)) == 0
    assert base.getpixel((9, 6)) == 255
    assert base.getpixel((10, 6)) == 0


# ---------------------------------------------------------------------------
# image/pure.py
# ---------------------------------------------------------------------------
def _decode_png(data):
    """用 pypng 解码，返回 (宽, 高, info, 行像素二维列表)。"""
    reader = png.Reader(file=io.BytesIO(data))
    width, height, rows, info = reader.read()
    return width, height, info, [list(row) for row in rows]


def test_tc_c_img_010_pypng_roundtrip_scenario():
    """TC-C-IMG-010（场景法）：PyPNG 后端端到端输出合法 1 位灰度 PNG，
    尺寸 290x290，静区为白(1)、定位眼为黑(0)，与 PIL 后端像素一致。"""
    buf = io.BytesIO()
    _make_qr(PyPNGImage, box_size=10, border=4).save(buf)
    data = buf.getvalue()
    assert data[:8] == PNG_SIGNATURE

    width, height, info, rows = _decode_png(data)
    assert (width, height) == (290, 290)
    assert info["greyscale"] is True
    assert info["bitdepth"] == 1
    assert len(rows) == 290 and all(len(r) == 290 for r in rows)
    # 首行静区全白；左上定位眼区域（含 4 模块静区偏移）为黑
    assert all(v == 1 for v in rows[0])
    assert rows[40][40] == 0

    # 跨后端一致性：同样参数下 PIL 与 PyPNG 静区/定位眼像素相同
    pil = _make_qr(PilImage, box_size=10, border=4).get_image()
    assert pil.getpixel((0, 0)) == 255
    assert pil.getpixel((40, 40)) == 0


def test_tc_c_img_011_pypng_save_path_closes_file_scenario(tmp_path):
    """TC-C-IMG-011（场景法，C-BUG-01 回归）：save(文件路径) 返回后
    文件句柄必须立即关闭——不产生 ResourceWarning，且 Windows 下
    文件可被立即删除，写出的内容仍是完整 PNG。"""
    path = tmp_path / "bug01.png"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        img = _make_qr(PyPNGImage)
        img.save(str(path))
        del img
        gc.collect()
    assert not any(issubclass(w.category, ResourceWarning) for w in caught), [
        str(w.message) for w in caught
    ]

    os.remove(str(path))  # 句柄未关闭时在 Windows 上会抛 PermissionError
    assert not path.exists()

    # 修复句柄问题不得损坏输出内容
    path2 = tmp_path / "bug01-content.png"
    _make_qr(PyPNGImage).save(str(path2))
    with open(path2, "rb") as f:
        assert f.read(8) == PNG_SIGNATURE


def test_tc_c_img_012_pypng_rejects_non_png_kind_equivalence():
    """TC-C-IMG-012（等价类，C-BUG-02 回归）：PyPNG 仅允许 PNG，
    传入其它 kind 必须抛 ValueError 且不写入任何字节；PNG/默认值正常。"""
    bad = io.BytesIO()
    with pytest.raises(ValueError):
        _make_qr(PyPNGImage).save(bad, kind="JPEG")
    assert bad.getvalue() == b""

    ok = io.BytesIO()
    _make_qr(PyPNGImage).save(ok, kind="PNG")
    assert ok.getvalue()[:8] == PNG_SIGNATURE

    default = io.BytesIO()
    _make_qr(PyPNGImage).save(default)
    assert default.getvalue()[:8] == PNG_SIGNATURE
