"""模块二 · 成员 A（编码与纠错）AI 生成并经技术审核的测试。

用例编号 TC-A-AI-01 起；候选来源与审核结论见
ai_records/AI-2026-09-20-成员A-编码与纠错AI测-01.md。
"""

import pytest

from qrcode import base, constants, exceptions, util


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


# TC-A-AI-05 字母数字与字节模式的字符计数位版本分组（边界值）
def test_length_in_bits_uses_mode_specific_version_groups():
    assert [util.length_in_bits(util.MODE_ALPHA_NUM, version) for version in (9, 10, 26, 27)] == [
        9,
        11,
        11,
        13,
    ]
    assert [util.length_in_bits(util.MODE_8BIT_BYTE, version) for version in (9, 10, 26, 27)] == [
        8,
        16,
        16,
        16,
    ]


# TC-A-AI-06 v1 各纠错等级的字节容量边界（边界值）
def test_version_one_capacity_changes_with_error_correction_level():
    expected_payload = {
        constants.ERROR_CORRECT_L: 17,
        constants.ERROR_CORRECT_M: 14,
        constants.ERROR_CORRECT_Q: 11,
        constants.ERROR_CORRECT_H: 7,
    }
    for level, payload_length in expected_payload.items():
        fitting = util.QRData(b"A" * payload_length, mode=util.MODE_8BIT_BYTE)
        assert len(util.create_data(1, level, [fitting])) == 26

        overflowing = util.QRData(b"A" * (payload_length + 1), mode=util.MODE_8BIT_BYTE)
        with pytest.raises(exceptions.DataOverflowError):
            util.create_data(1, level, [overflowing])


# TC-A-AI-07 数据终止、补零与交替填充码字（场景法）
def test_create_data_applies_terminator_zero_padding_and_pad_codewords():
    encoded = util.create_data(
        1,
        constants.ERROR_CORRECT_L,
        [util.QRData(b"A", mode=util.MODE_8BIT_BYTE)],
    )

    assert encoded[:19] == [
        64,
        20,
        16,
        236,
        17,
        236,
        17,
        236,
        17,
        236,
        17,
        236,
        17,
        236,
        17,
        236,
        17,
        236,
        17,
    ]


# TC-A-AI-08 不等长 RS 块的数据与纠错码字交织（场景法）
def test_create_bytes_interleaves_unequal_rs_blocks_in_column_order():
    buffer = util.BitBuffer()
    for value in (1, 2, 3, 4, 5):
        buffer.put(value, 8)

    blocks = [base.RSBlock(3, 2), base.RSBlock(4, 3)]
    assert util.create_bytes(buffer, blocks) == [1, 3, 2, 4, 5, 3, 2]
