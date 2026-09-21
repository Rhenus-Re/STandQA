"""模块二 · 成员 A（编码与纠错）AI 生成并经技术审核的测试。

用例编号 TC-A-AI-01 起；候选来源与审核结论见
ai_records/AI-2026-09-20-成员A-编码与纠错AI测-01.md。
"""

import pytest

from qrcode import QRCode, base, constants, exceptions, util


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


# TC-A-AI-09 有限域指数表以 255 为周期（等价类）
def test_gexp_repeats_after_galois_field_period():
    assert base.gexp(0) == base.gexp(255) == 1
    assert base.gexp(1) == base.gexp(256) == 2
    assert base.gexp(254) == 142


# TC-A-AI-10 有限域多项式乘法参考向量（等价类）
def test_polynomial_multiplication_matches_galois_field_vector():
    left = base.Polynomial([1, 2], 0)
    right = base.Polynomial([1, 3], 0)
    assert list(left * right) == [1, 1, 6]


# TC-A-AI-11 BCH 格式与版本信息新增向量（等价类）
def test_bch_type_vectors_cover_additional_format_and_version_values():
    assert util.BCH_type_info(0) == 0b101010000010010
    assert util.BCH_type_info(3) == 0b101101101001011
    assert util.BCH_type_number(10) == 0b001010010011010011
    assert util.BCH_type_number(40) == 0b101000110001101001


# TC-A-AI-12 校正图案位置查表结果（边界值）
def test_pattern_position_returns_known_version_coordinates():
    assert util.pattern_position(1) == []
    assert util.pattern_position(2) == [6, 18]
    assert util.pattern_position(7) == [6, 22, 38]
    assert util.pattern_position(40) == [6, 30, 58, 86, 114, 142, 170]


# TC-A-AI-13 2×2 同色方块惩罚规则（等价类）
def test_lost_point_level2_penalizes_a_dark_two_by_two_block():
    modules = [[True, True], [True, True]]
    assert util._lost_point_level2(modules, 2) == 3


# TC-A-AI-14 1011101 模式惩罚规则（场景法）
def test_lost_point_level3_penalizes_finder_like_horizontal_pattern():
    modules = [[False] * 11 for _ in range(11)]
    modules[5] = [False, False, False, False, True, False, True, True, True, False, True]
    assert util._lost_point_level3(modules, 11) == 40


# TC-A-AI-15 深色模块比例惩罚规则（边界值）
def test_lost_point_level4_penalizes_all_dark_matrix():
    modules = [[True] * 10 for _ in range(10)]
    assert util._lost_point_level4(modules, 10) == 100


# TC-A-AI-16 零分段阈值拒绝，避免零长度匹配循环（缺陷 M2-A-01 回归）
def test_optimal_data_chunks_rejects_zero_minimum():
    with pytest.raises(ValueError, match="positive integer"):
        list(util.optimal_data_chunks(b"!", minimum=0))


# TC-A-AI-17 负分段阈值拒绝（缺陷 M2-A-01 回归）
def test_optimal_data_chunks_rejects_negative_minimum():
    with pytest.raises(ValueError, match="positive integer"):
        list(util.optimal_data_chunks(b"!", minimum=-1))


# TC-A-AI-18 add_data 传入负 optimize 时给出明确错误（缺陷 M2-A-01 回归）
def test_add_data_rejects_negative_optimize_before_regex_compilation():
    qr = QRCode()
    with pytest.raises(ValueError, match="positive integer"):
        qr.add_data(b"!", optimize=-1)


# TC-A-AI-19 最小有效阈值可完成字节模式分段（缺陷 M2-A-01 对照）
def test_optimal_data_chunks_with_minimum_one_finishes_for_byte_input():
    chunks = list(util.optimal_data_chunks(b"!", minimum=1))
    assert [(chunk.mode, chunk.data) for chunk in chunks] == [(util.MODE_8BIT_BYTE, b"!")]


# TC-A-AI-20 optimize=0 仍关闭分段优化（缺陷 M2-A-01 兼容性）
def test_add_data_zero_optimize_preserves_existing_no_split_behavior():
    qr = QRCode()
    qr.add_data(b"!", optimize=0)
    assert [(chunk.mode, chunk.data) for chunk in qr.data_list] == [(util.MODE_8BIT_BYTE, b"!")]


# TC-A-AI-21 非整数分段阈值拒绝（缺陷 M2-A-01 边界）
def test_optimal_data_chunks_rejects_noninteger_minimum():
    with pytest.raises(ValueError, match="positive integer"):
        list(util.optimal_data_chunks(b"!", minimum=1.5))
