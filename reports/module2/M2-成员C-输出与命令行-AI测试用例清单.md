# 模块二成员 C 输出与命令行 AI 测试用例清单

全部用例由 AI 辅助生成、人工审核修订后采纳，编号 TC-C-AI-01 ~ TC-C-AI-08，参数化后共 16 个 pytest 项；与模块一人工用例 TC-C-001~012 的断言对象不重复。实现位置：`tests/ai_generated/test_output_cli_ai.py`；逐条审核记录见 `ai_records/AI-2026-09-18-成员C-输出与命令行AI测-01.md`。

| 编号 | 测试点 | 方法 | 结果 |
| --- | --- | --- | --- |
| TC-C-AI-01 | PilImage.save 的 kind 参数映射 PIL 输出格式（默认 PNG，kind="JPEG" 产出真 JPEG） | 等价类 | 通过 |
| TC-C-AI-02 | SVG width/height 与 viewBox 的 mm 换算，box_size=1/3/5（2.9/8.7/14.5mm） | 边界值（参数化 3 项） | 通过 |
| TC-C-AI-03 | SvgFragmentImage 片段输出：无 XML 声明、命名空间根元素、version=1.1 | 场景法 | 通过 |
| TC-C-AI-04 | CLI --factory 内置后端矩阵：png / svg-fragment / svg-path 端到端产物 | 场景法 | 通过 |
| TC-C-AI-05 | CLI --error-correction 的 L/M/Q/H 全值域与非法值 X 友好退出 | 等价类（参数化 5 项） | 通过 |
| TC-C-AI-06 | print_ascii 静区奇偶边界：border=1/2/3 的行数与行宽公式 | 边界值（参数化 3 项） | 通过 |
| TC-C-AI-07 | print_ascii(tty=True) 的 ANSI 着色契约（强制 invert、前景码、末行无背景码） | 场景法 | 通过 |
| TC-C-AI-08 | CLI --factory 无效值统一友好错误（缺陷 M2-C-01 回归） | 等价类 | 通过 |

复核声明：以上结果为修复缺陷 M2-C-01 后的实际运行结果（58 项通过，含模块一 42 项基线），不存在未经运行确认的用例。
