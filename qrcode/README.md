# 被测源码说明

本目录包含课程作业使用的 `lincolnloop/python-qrcode` 被测源码。

- 上游仓库：<https://github.com/lincolnloop/python-qrcode>
- 固定标签：`v8.2`
- 上游 commit：`3704f57a1107dbf553a50f5b531da3859abe19cf`
- 上游许可：BSD-3-Clause，详见本目录的 `LICENSE`
- 导入日期：2026-09-08

## 导入范围

本目录导入了上游 `qrcode/` Python 包的运行源码，包括编码、矩阵生成、图像输出、样式和命令行入口。

上游自带的 `qrcode/tests/` 未导入，避免与本课程的人工测试和 AI 测试混放。课程测试分别存放在根目录的 `tests/manual/` 和 `tests/ai_generated/`。

除本说明文件和复制的许可证外，其余文件保持上游 `v8.2` 内容不变。后续如需修改被测源码，应通过独立修复提交记录修改原因、关联缺陷和回归结果。
