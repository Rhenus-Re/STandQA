# 模块二成员 C 输出与命令行缺陷清单

## M2-C-01 CLI --factory 非法路径未友好处理

| 项 | 内容 |
| --- | --- |
| 测试人 | 成员 C（2026.09.18 发现，2026.09.21 回归关闭） |
| 功能模块名 | console_scripts.main / get_factory |
| 功能编号 | qrcode/console_scripts.py |
| 测试项编号 | TC-C-AI-08 |
| 缺陷标题 | CLI --factory 带点非法路径抛未捕获异常，与同类输入的错误处理不一致 |
| 严重程度 | 低（Minor） |
| 优先级 | 中 |
| 状态 | 已关闭 |
| 分配给 | 成员 C |
| 发送给 | 成员 B（交叉复现） |
| 预期结果 | 所有无效 --factory 输入均以 SystemExit 2 加使用说明退出（与 --factory foo、--error-correction X 的行为一致） |
| 实际结果 | --factory pil.PilImage 抛 ModuleNotFoundError、--factory qrcode.image.pil.NoSuchImage 抛 AttributeError 的原始 traceback；退出码非 2、无使用说明 |
| 复现步骤 | `python -m qrcode.console_scripts --factory pil.PilImage hello` |
| 根因 | `main()` 的 try 块仅捕获 ValueError；`get_factory()` 内裸 `__import__` 与 `getattr` 对带点非法路径抛出的 ImportError / AttributeError 未被转换成友好错误 |
| 修复 | try 块补充 `except (ImportError, AttributeError)` → `raise_error()`（提交 6550125） |
| 回归验证 | TC-C-AI-08 通过；成员 C 口径 58 项、分支全量 89 项全部通过 |

## 候选预期修正记录

AI 初稿的两处错误预期经人工运行修正，未计入缺陷：

1. TC-C-AI-01：AI 误以为 PilImage 与 PyPNGImage 一样校验 kind 而预期 kind="JPEG" 抛 ValueError；实际 PilImage 不经 check_kind，直接映射 PIL format 产出真 JPEG，预期结果据此修正。
2. TC-C-AI-07：AI 假设 tty 输出每行均含背景码 48;5;232；比对源码发现末行（r=modcount+border-1）不写背景码，断言改为「背景码仅出现在非末行」并保留末行反向断言。

上述内容均不属于 GitHub Issue、功能建议或正常抛出的异常，未重复计入缺陷数量。
