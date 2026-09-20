"""模块二 · 成员 A（编码与纠错）AI 生成并经技术审核的测试。

用例编号 TC-A-AI-01 起；候选来源与审核结论见
ai_records/AI-2026-09-20-成员A-编码与纠错AI测-01.md。
"""

import pytest

from qrcode import util


def _bits(buffer):
    return "".join("1" if buffer.get(index) else "0" for index in range(len(buffer)))


# TC-A-AI-01 UTF-8 文本转字节（等价类）
def test_to_bytestring_encodes_unicode_text_as_utf8():
    assert util.to_bytestring("二维码") == "二维码".encode("utf-8")
    raw = b"already-bytes"
    assert util.to_bytestring(raw) is raw


# TC-A-AI-02 显式模式与数据不兼容时拒绝（等价类）
def test_qrdata_rejects_data_that_cannot_use_requested_mode():
    with pytest.raises(ValueError, match="can not be represented"):
        util.QRData(b"12A", mode=util.MODE_NUMBER)
    with pytest.raises(ValueError, match="can not be represented"):
        util.QRData(b"lowercase", mode=util.MODE_ALPHA_NUM)


# TC-A-AI-03 数字模式单字符尾数使用 4 位（边界值）
def test_numeric_qrdata_single_digit_uses_four_bits():
    buffer = util.BitBuffer()
    util.QRData(b"7", mode=util.MODE_NUMBER).write(buffer)

    assert len(buffer) == 4
    assert _bits(buffer) == "0111"


# TC-A-AI-04 字母数字模式奇数长度尾数使用 6 位（边界值）
def test_alphanumeric_qrdata_odd_tail_uses_six_bits():
    buffer = util.BitBuffer()
    util.QRData(b"AB1", mode=util.MODE_ALPHA_NUM).write(buffer)

    assert len(buffer) == 17
    assert _bits(buffer) == "00111001101000001"
