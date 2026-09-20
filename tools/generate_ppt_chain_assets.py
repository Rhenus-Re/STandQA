"""Generate real python-qrcode outputs and trace data for the module-one PPT."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import platform
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import qrcode
from qrcode import constants, util
from qrcode.image.svg import SvgPathImage


ASSET_ROOT = PROJECT_ROOT / "reports" / "module1" / "ppt-assets"
DEFAULT_PAYLOAD = "HUST-STandQA-2026"
DEFAULT_ASSET_NAME = "qr-chain"


MODE_NAMES = {
    util.MODE_NUMBER: "NUMBER",
    util.MODE_ALPHA_NUM: "ALPHANUMERIC",
    util.MODE_8BIT_BYTE: "BYTE",
    util.MODE_KANJI: "KANJI",
}


def matrix_to_bits(matrix: list[list[bool]]) -> str:
    return "\n".join("".join("1" if cell else "0" for cell in row) for row in matrix) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate real python-qrcode outputs and trace data for PPT assets."
    )
    parser.add_argument("--payload", default=DEFAULT_PAYLOAD, help="Text or URL to encode.")
    parser.add_argument(
        "--asset-name",
        default=DEFAULT_ASSET_NAME,
        help="Name of the output folder under reports/module1/ppt-assets.",
    )
    args = parser.parse_args()
    if not args.asset_name or any(char in args.asset_name for char in "\\\\/:"):
        parser.error("--asset-name must be a simple folder name.")
    return args


def main() -> None:
    args = parse_args()
    payload = args.payload
    output_dir = ASSET_ROOT / args.asset_name
    output_dir.mkdir(parents=True, exist_ok=True)

    qr = qrcode.QRCode(
        version=None,
        error_correction=constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    selected_mask = qr.best_mask_pattern()
    qr.make(fit=False)

    matrix_without_border = qr.modules
    matrix_with_border = qr.get_matrix()
    matrix_bits = matrix_to_bits(matrix_without_border)

    png_path = output_dir / "03-output-png.png"
    svg_path = output_dir / "04-output-svg.svg"
    ascii_path = output_dir / "05-output-ascii.txt"
    matrix_png_path = output_dir / "02-matrix.png"

    qr.make_image().save(str(png_path))
    qr.make_image(image_factory=SvgPathImage).save(str(svg_path))

    ascii_output = io.StringIO()
    qr.print_ascii(out=ascii_output, invert=False)
    ascii_path.write_text(ascii_output.getvalue(), encoding="utf-8")

    matrix_qr = qrcode.QRCode(
        version=qr.version,
        error_correction=constants.ERROR_CORRECT_M,
        box_size=12,
        border=0,
        mask_pattern=selected_mask,
    )
    matrix_qr.add_data(payload)
    matrix_qr.make(fit=False)
    matrix_qr.make_image().save(str(matrix_png_path))

    chunks = []
    for chunk in qr.data_list:
        data = bytes(chunk.data)
        chunks.append(
            {
                "mode": MODE_NAMES.get(chunk.mode, str(chunk.mode)),
                "utf8_text": data.decode("utf-8"),
                "byte_length": len(data),
                "hex": data.hex(" ").upper(),
            }
        )

    trace = {
        "purpose": "模块一成果汇报PPT：二维码生成风险链路的可复查素材",
        "input": {
            "text": payload,
            "character_length": len(payload),
            "utf8_byte_length": len(payload.encode("utf-8")),
            "utf8_hex": payload.encode("utf-8").hex(" ").upper(),
        },
        "encoding": {
            "chunks": chunks,
            "error_correction": "M",
            "selected_version": qr.version,
            "selected_mask_pattern": selected_mask,
            "final_codeword_count": len(qr.data_cache),
            "final_codewords_hex": " ".join(f"{codeword:02X}" for codeword in qr.data_cache),
        },
        "matrix": {
            "modules_per_side": qr.modules_count,
            "matrix_without_border_file": "01-matrix-bits.txt",
            "matrix_without_border_sha256": hashlib.sha256(matrix_bits.encode("ascii")).hexdigest(),
            "matrix_with_border_side": len(matrix_with_border),
        },
        "outputs": {
            "matrix_png": matrix_png_path.name,
            "png": png_path.name,
            "svg": svg_path.name,
            "ascii": ascii_path.name,
        },
        "environment": {
            "python": platform.python_version(),
            "source": "当前仓库中的 qrcode 代码",
        },
    }

    (output_dir / "00-input.txt").write_text(payload + "\n", encoding="utf-8")
    (output_dir / "01-matrix-bits.txt").write_text(matrix_bits, encoding="ascii")
    (output_dir / "trace.json").write_text(
        json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "README.md").write_text(
        "# 二维码生成链路 PPT 素材\n\n"
        "本目录中的 PNG、SVG 和 ASCII 文件均由仓库当前的 `qrcode` 代码生成，"
        f"输入固定为 `{payload}`。`trace.json` 保存输入、编码模式、版本、"
        "掩码、最终码字和矩阵尺寸；`01-matrix-bits.txt` 保存不含静区的真实模块矩阵。\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
