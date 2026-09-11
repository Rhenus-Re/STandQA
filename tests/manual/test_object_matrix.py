"""模块一 · 成员 B（对象与矩阵）人工测试。

被测源码：`qrcode/main.py`（对象与矩阵逻辑）、`qrcode/exceptions.py`。
用例编号 TC-B-01 ~ TC-B-12，覆盖等价类、边界值、场景法三种方法。
"""

import pytest

from qrcode import QRCode, constants, exceptions
from qrcode import util
from qrcode.util import QRData


# TC-B-01 构造参数校验：version 合法值（等价类）
@pytest.mark.parametrize("version", [1, 40])
def test_version_valid_range(version):
    assert QRCode(version=version).version == version


# TC-B-02 构造参数校验：version 边界外（边界值）
@pytest.mark.parametrize("version", [0, 41, -1])
def test_version_invalid_raises(version):
    with pytest.raises(ValueError):
        QRCode(version=version)


# TC-B-03 box_size / border 校验（等价类）
def test_box_size_and_border_validation():
    with pytest.raises(ValueError):
        QRCode(box_size=0)
    with pytest.raises(ValueError):
        QRCode(box_size=-1)
    with pytest.raises(ValueError):
        QRCode(border=-1)
    qr = QRCode(box_size=2, border=0)
    assert qr.box_size == 2 and qr.border == 0


# TC-B-04 mask_pattern 校验（等价类 + 边界值）
def test_mask_pattern_validation():
    for pattern in range(8):
        assert QRCode(mask_pattern=pattern).mask_pattern == pattern
    with pytest.raises(TypeError):
        QRCode(mask_pattern="0")
    for pattern in (-1, 8):
        with pytest.raises(ValueError):
            QRCode(mask_pattern=pattern)


# TC-B-05 add_data 支持 str/bytes/QRData（等价类）
def test_add_data_types():
    qr = QRCode()
    qr.add_data("abc")
    qr.add_data(b"def")
    qr.add_data(QRData("123"))
    assert len(qr.data_list) == 3
    assert qr.data_cache is None


# TC-B-06 make() 自动版本适配（场景法）
def test_make_auto_fit_version():
    small = QRCode()
    small.add_data("hi")
    small.make()
    big = QRCode()
    big.add_data("x" * 1000)
    big.make()
    assert small.version == 1
    assert big.version > small.version


# TC-B-07 make() 固定版本与矩阵尺寸（场景法）
def test_make_fixed_version_modules_count():
    qr = QRCode(version=5)
    qr.add_data("data")
    qr.make(fit=False)
    assert qr.modules_count == 5 * 4 + 17


# TC-B-08 数据溢出（边界值）
def test_data_overflow():
    qr = QRCode(
        version=1,
        error_correction=constants.ERROR_CORRECT_L,
        mask_pattern=0,
    )
    qr.add_data("x" * 1000)
    with pytest.raises(exceptions.DataOverflowError):
        qr.make(fit=False)


# TC-B-09 clear() 与对象复用（场景法，含缺陷 B-01）
def test_clear_resets_for_reuse():
    qr = QRCode()
    qr.add_data("x" * 1000)
    qr.make()
    qr.clear()
    assert qr.data_list == []
    assert qr.data_cache is None
    qr.add_data("y")
    qr.make()
    # 缺陷 B-01：clear() 未重置自动适配的版本，复用后应回到最小版本 1
    assert qr.version == 1


# TC-B-10 掩码选择影响矩阵，自动选择落在 0-7（等价类）
def test_mask_pattern_affects_matrix():
    matrices = []
    for pattern in (0, 1):
        qr = QRCode(mask_pattern=pattern)
        qr.add_data("same")
        qr.make()
        matrices.append(qr.modules)
    assert matrices[0] != matrices[1]

    qr = QRCode()
    qr.add_data("auto")
    assert 0 <= qr.best_mask_pattern() <= 7


# TC-B-11 定位/校正图案放置（场景法）
def test_pattern_placement():
    qr = QRCode(version=2)
    qr.add_data("pattern")
    qr.make()
    assert qr.modules_count == 2 * 4 + 17
    assert util.pattern_position(2) == [6, 18]
    # 定位图案中心（0,0 附近 3x3 深色块）
    assert qr.modules[2][2] is True
    # version 2 唯一独立校正图案中心 (18,18)
    assert qr.modules[18][18] is True


# TC-B-12 get_matrix() 边框与矩阵返回（场景法，含缺陷 B-02）
def test_get_matrix_border():
    qr = QRCode(box_size=1, border=3)
    qr.add_data("hello")
    qr.make()
    matrix = qr.get_matrix()
    size = qr.modules_count + 2 * 3
    assert len(matrix) == size
    assert len(matrix[0]) == size
    # 缺陷 B-02：边框行应为独立列表，修改一行不应影响另一行
    assert matrix[0] is not matrix[1]
    matrix[0][0] = True
    assert matrix[1][0] is False
    # border=0 返回无边框矩阵
    qr.border = 0
    assert len(qr.get_matrix()) == qr.modules_count
