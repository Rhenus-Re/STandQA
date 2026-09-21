# 模块二成员 C 输出与命令行基线测试记录

## 基线来源

- 工作分支：`member-c/module2-output-ai`
- 创建起点：`origin/member-a/module2-encoding-ai`（`3724672`）
- 基线口径：仅模块一人工测试（成员 C 既往 12 条用例所在的 `tests/manual` 共 42 个 pytest 项）。分支同时携带成员 A、成员 B 的模块二 AI 用例，但不计入成员 C 的比较基线。

## 执行命令与结果

```powershell
python -m pytest tests\manual -q
```

结果：42 项通过，耗时 0.56 秒。

基线语句覆盖率（coverage 7.1.0，python 3.11.9）：

| 范围 | 语句覆盖率 |
|---|---|
| qrcode 全包 | 73% |
| qrcode/console_scripts.py | 74% |
| qrcode/image/svg.py | 93% |
| qrcode/image/pil.py | 85% |
| qrcode/image/pure.py | 97% |

成员 C 的模块二新增 AI 用例加入后，将与该 42 项基线合并统计（42 + 16 = 58 项）。
