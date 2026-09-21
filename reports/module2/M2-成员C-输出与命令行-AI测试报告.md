# 模块二成员 C 输出与命令行 AI 测试报告

## 范围

模块二采用方案 2（AI 测），在成员 C 的输出与命令行测试域生成新增用例与自动化脚本，并辅助缺陷定位与回归；不改变被测对象。基线为模块一人工测试 42 项（见 `M2-成员C-输出与命令行-基线测试记录.md`），全部用例与模块一不重复。

新增覆盖点：PilImage 保存格式参数、SVG 单位换算、SvgFragmentImage 片段后端、CLI 内置 --factory 后端矩阵、CLI --error-correction 值域、print_ascii 静区奇偶边界、print_ascii(tty=True) ANSI 契约、CLI --factory 无效值错误处理（缺陷 M2-C-01 回归）。

## 环境与命令

- 环境：Windows x64；Python 3.11.9、pytest 8.4.2、pytest-cov 7.1.0、python-qrcode v8.2、Pillow 12.3.0、PyPNG 0.20220715.0
- 用例生成：Trae（GLM 编码智能体），记录见 `ai_records/AI-2026-09-18-成员C-输出与命令行AI测-01.md`
- 执行命令：

```powershell
python -m pytest tests\manual tests\ai_generated\test_output_cli_ai.py -q --cov=qrcode
```

## 执行结果

| 范围 | pytest 项数 | 结果 |
| --- | --- | --- |
| 模块一人工测试 | 42 | 全部通过 |
| 成员 C 模块二 AI 测试 | 16 | 全部通过 |
| 合计（成员 C 口径） | 58 | 全部通过 |

缺陷 M2-C-01 已修复并通过回归；分支同时携带成员 A、成员 B 的模块二 AI 用例，合并后全量 89 项亦全部通过。

覆盖率（coverage 7.1.0，明细见 `M2-成员C-输出与命令行-coverage.xml`）：

| 范围 | 基线 42 项 | 42 + AI 16 项 |
| --- | --- | --- |
| qrcode 全包 | 73% | 74% |
| qrcode/console_scripts.py | 74% | 80% |
| qrcode/image/svg.py | 93% | 99% |
| qrcode/main.py | 93% | 95% |

## 结论

成员 C 输出与命令行域新增 8 条用例（参数化后 16 项）全部有效且不与模块一重复；AI 辅助定位缺陷 M2-C-01 一处，已修复并回归。输出与命令行域的关键文件（console_scripts.py、image/svg.py）覆盖率明显提升，模块二测试目标达成。
