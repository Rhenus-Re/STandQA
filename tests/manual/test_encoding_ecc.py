"""模块一 · 成员 A（编码与纠错）候选测试工作稿。

范围：qrcode/util.py、qrcode/base.py、qrcode/LUT.py、qrcode/constants.py。
用例编号：TC-A-01 至 TC-A-12；设计方法覆盖等价类、边界值和场景法。

提交课程前，成员 A 必须独立审阅、重写并确认本文件中的测试设计，
才可将其作为“模块一人工测试”成果提交。
"""

import pytest

from qrcode import LUT, base, constants, exceptions, util


def _bits(buffer):
    """将 BitBuffer 的有效位转换成便于断言的 0/1 字符串。"""
    return "".join("1" if buffer.get(index) else "0" for index in range(len(buffer)))


# TC-A-01 编码模式识别：数字、字母数字、字节（等价类）
def test_optimal_mode_for_three_data_classes():
    assert util.optimal_mode(b"012345") == util.MODE_NUMBER
    assert util.optimal_mode(b"A1 $%") == util.MODE_ALPHA_NUM
    assert util.optimal_mode(b"lower-case") == util.MODE_8BIT_BYTE


# TC-A-02 数据分段：连续字母数字段和字节段（场景法）
def test_optimal_data_chunks_separates_alphanumeric_and_byte_data():
    chunks = list(util.optimal_data_chunks(b"ABCD1234abcd", minimum=4))

    assert [(chunk.mode, chunk.data) for chunk in chunks] == [
        (util.MODE_ALPHA_NUM, b"ABCD"),
        (util.MODE_NUMBER, b"1234"),
        (util.MODE_8BIT_BYTE, b"abcd"),
    ]


# TC-A-03 数据分段阈值：恰好 minimum 个数字才拆为数字段（边界值）
def test_optimal_data_chunks_respects_minimum_split_boundary():
    chunks = list(util.optimal_data_chunks(b"abc1234XYZ", minimum=4))

    assert [(chunk.mode, chunk.data) for chunk in chunks] == [
        (util.MODE_8BIT_BYTE, b"abc"),
        (util.MODE_NUMBER, b"1234"),
        (util.MODE_8BIT_BYTE, b"XYZ"),
    ]


# TC-A-04 QRData 数字模式写入：三位组与余数位（边界值）
def test_qrdata_numeric_write_uses_required_bit_lengths():
    buffer = util.BitBuffer()
    util.QRData(b"12345", mode=util.MODE_NUMBER).write(buffer)

    assert len(buffer) == 17
    assert _bits(buffer) == "00011110110101101"


# TC-A-05 QRData 字母数字模式写入：两字符组合为 11 位（等价类）
def test_qrdata_alphanumeric_write_combines_two_characters():
    buffer = util.BitBuffer()
    util.QRData(b"A1", mode=util.MODE_ALPHA_NUM).write(buffer)

    assert len(buffer) == 11
    assert _bits(buffer) == "00111000011"


# TC-A-06 BitBuffer 跨字节写入和读取（边界值）
def test_bitbuffer_crosses_byte_boundary_without_losing_bit_order():
    buffer = util.BitBuffer()
    buffer.put(0b101, 3)
    buffer.put_bit(False)
    buffer.put(0b11110000, 8)

    assert len(buffer) == 12
    assert buffer.buffer == [0b10101111, 0b00000000]
    assert _bits(buffer) == "101011110000"


# TC-A-07 字符计数位：版本组 1/9、10/26、27/40 边界（边界值）
def test_length_in_bits_changes_at_qr_version_groups():
    assert [util.length_in_bits(util.MODE_NUMBER, version) for version in (1, 9)] == [
        10,
        10,
    ]
    assert [util.length_in_bits(util.MODE_NUMBER, version) for version in (10, 26)] == [
        12,
        12,
    ]
    assert [util.length_in_bits(util.MODE_NUMBER, version) for version in (27, 40)] == [
        14,
        14,
    ]


# TC-A-08 容量边界：v1-M 的 14 个字节可编码、15 个字节溢出（边界值）
def test_create_data_enforces_version_one_medium_capacity():
    fitting = util.QRData(b"A" * 14, mode=util.MODE_8BIT_BYTE)
    encoded = util.create_data(1, constants.ERROR_CORRECT_M, [fitting])

    assert len(encoded) == 26
    overflowing = util.QRData(b"A" * 15, mode=util.MODE_8BIT_BYTE)
    with pytest.raises(exceptions.DataOverflowError):
        util.create_data(1, constants.ERROR_CORRECT_M, [overflowing])


# TC-A-09 RS 块与校正图案对非法版本应一致拒绝（等价类，缺陷 A-01 回归）
@pytest.mark.parametrize("version", [0, 41])
def test_low_level_version_helpers_reject_out_of_range_versions(version):
    with pytest.raises(ValueError, match="expected 1 to 40"):
        base.rs_blocks(version, constants.ERROR_CORRECT_M)
    with pytest.raises(ValueError, match="expected 1 to 40"):
        util.pattern_position(version)


# TC-A-10 RS 分组与纠错生成多项式（场景法）
def test_rs_blocks_and_generator_polynomial_match_lookup_table():
    blocks = base.rs_blocks(5, constants.ERROR_CORRECT_Q)
    assert [(block.total_count, block.data_count) for block in blocks] == [
        (33, 15),
        (33, 15),
        (34, 16),
        (34, 16),
    ]

    generator = base.Polynomial([1], 0)
    for exponent in range(7):
        generator = generator * base.Polynomial([1, base.gexp(exponent)], 0)
    assert list(generator) == LUT.rsPoly_LUT[7]


# TC-A-11 BCH：格式信息和版本信息的已知编码向量（等价类）
def test_bch_type_info_and_version_number_vectors():
    # L 级纠错、掩码 0 的格式信息；版本 7 的版本信息（ISO/IEC 18004）。
    assert util.BCH_type_info(constants.ERROR_CORRECT_L << 3) == 0b111011111000100
    assert util.BCH_type_number(7) == 0b000111110010010100


# TC-A-12 八种掩码公式与全黑矩阵惩罚评分（场景法）
def test_mask_functions_and_lost_point_score():
    expected = [False, False, False, True, True, False, True, False]
    assert [util.mask_func(pattern)(1, 2) for pattern in range(8)] == expected

    full_dark = [[True] * 5 for _ in range(5)]
    assert util.lost_point(full_dark) == 178
