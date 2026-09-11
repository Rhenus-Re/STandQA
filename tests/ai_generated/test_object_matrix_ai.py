"""模块二 · 成员 B（对象与矩阵）AI 生成并经人工审核的测试。

用例编号 TC-B-AI-01 ~ TC-B-AI-08，与模块一 TC-B-* 不重复。
每条用例的审核结论见 ai_records/。
"""

import pytest

from qrcode import QRCode, constants


# TC-B-AI-01 error_correction 合法值域与非法值（边界值，缺陷 B-03）
def test_error_correction_valid_and_invalid():
    for ec in (
        constants.ERROR_CORRECT_L,
        constants.ERROR_CORRECT_M,
        constants.ERROR_CORRECT_Q,
        constants.ERROR_CORRECT_H,
    ):
        qr = QRCode(error_correction=ec)
        qr.add_data("x")
        qr.make()
        assert qr.error_correction == ec
    with pytest.raises(ValueError):
        QRCode(error_correction=4)


# TC-B-AI-02 add_data 的 optimize 参数（等价类）
def test_add_data_optimize_split():
    qr_opt = QRCode()
    qr_opt.add_data("abcde12345", optimize=3)
    qr_no = QRCode()
    qr_no.add_data("abcde12345", optimize=0)
    assert len(qr_opt.data_list) == 2
    assert len(qr_no.data_list) == 1


# TC-B-AI-03 version 属性惰性适配（场景法）
def test_version_lazy_best_fit():
    qr = QRCode()
    qr.add_data("x" * 500)
    assert qr.version > 1


# TC-B-AI-04 对象复用后追加数据版本增长（场景法）
def test_reuse_append_grows_version():
    qr = QRCode()
    qr.add_data("hi")
    qr.make()
    v1 = qr.version
    qr.add_data("x" * 1000)
    qr.make()
    assert qr.version > v1


# TC-B-AI-05 border=0 时 get_matrix 直接返回内部矩阵（边界值）
def test_get_matrix_border_zero_returns_modules():
    qr = QRCode(border=0)
    qr.add_data("hello")
    qr.make()
    matrix = qr.get_matrix()
    assert matrix is qr.modules
    assert len(matrix) == qr.modules_count


# TC-B-AI-06 add_data 后 data_cache 失效（等价类）
def test_data_cache_invalidated_on_add():
    qr = QRCode()
    qr.add_data("hi")
    qr.make()
    assert qr.data_cache is not None
    qr.add_data("there")
    assert qr.data_cache is None


# TC-B-AI-07 fit=False 保留显式版本（等价类）
def test_fit_false_preserves_explicit_version():
    qr = QRCode(version=7)
    qr.add_data("hi")
    qr.make(fit=False)
    assert qr.version == 7
    assert qr.modules_count == 7 * 4 + 17


# TC-B-AI-08 get_matrix 不同 border 边框宽度（等价类）
@pytest.mark.parametrize("border", [0, 1, 4])
def test_get_matrix_border_width(border):
    qr = QRCode(border=border)
    qr.add_data("hello")
    qr.make()
    matrix = qr.get_matrix()
    assert len(matrix) == qr.modules_count + 2 * border
    assert len(matrix[0]) == qr.modules_count + 2 * border
