# 模块一 成员C 缺陷清单——输出与命令行域

被测版本：python-qrcode v8.2（commit `3704f57`）。本缺陷由成员C人工分析源码
并运行最小复现确认，**不属于 GitHub Issue、功能建议或正常抛出的异常**：
`print_tty` 本应依据 `self.border` 渲染静区，却将静区写死为 1 模块，属于
"本应遵循配置却忽略配置"的行为错误。

## C-BUG-01：print_tty 忽略 self.border，静区被硬编码为 1 模块

| 项 | 内容 |
|---|---|
| 严重程度 | 一般（Major）：输出与配置不符，静区不满足 QR 规范 ≥4 模块要求，影响可扫描性 |
| 发现用例 | TC-C-011（回归用例） |
| 缺陷位置 | `qrcode/main.py` `QRCode.print_tty` |

**现象**

`print_tty` 输出的可见行宽与 `self.border` 无关：无论 `border` 设为 4（默认）
还是其它值，每侧静区固定渲染 1 模块（2 字符）。默认 `border=4`、`version=1`
（modcount=21）时，行可见宽度为 46，而期望为 58（`21*2 + 4*4`）。
对照 `print_ascii` 使用 `range(-self.border, modcount+self.border, ...)` 正确遵循
`self.border`，两者不一致，可佐证 `print_tty` 行为错误。

**最小复现**

```python
import re, io
import qrcode

qr = qrcode.QRCode(version=1, box_size=1, border=4)
qr.add_data("M1")
qr.make()

class FakeTty:
    def __init__(self): self.buf = []
    def write(self, s): self.buf.append(s)
    def flush(self): pass
    def isatty(self): return True

ft = FakeTty()
qr.print_tty(out=ft)
visible = re.sub(r"\x1b\[[0-9;]*m", "", "".join(ft.buf))
widths = {len(l) for l in visible.split("\n") if l}
print(widths)            # 修复前：{46}，期望 {58}
print(qr.modules_count * 2 + qr.border * 4)   # 58
```

**根因**

修复前实现（`main.py` 第 273–283 行）：

```python
modcount = self.modules_count
out.write("\x1b[1;47m" + (" " * (modcount * 2 + 4)) + "\x1b[0m\n")   # +4 写死
for r in range(modcount):
    out.write("\x1b[1;47m  \x1b[40m")          # 左静区固定 2 字符（1 模块）
    for c in range(modcount):
        ...
    out.write("\x1b[1;47m  \x1b[0m\n")         # 右静区固定 2 字符（1 模块）
out.write("\x1b[1;47m" + (" " * (modcount * 2 + 4)) + "\x1b[0m\n")
```

顶/底边行宽 `modcount*2 + 4` 与每行左右静区 `"  "`（2 字符）均硬编码，
完全未引用 `self.border`。`self.border` 默认为 4，正确宽度应为
`modcount*2 + self.border*4`。

**修复**

引入 `quiet_zone = self.border * 2`（每侧可见字符数），顶/底边与左右静区均使用
`quiet_zone`：

```python
modcount = self.modules_count
quiet_zone = self.border * 2
out.write("\x1b[1;47m" + (" " * (modcount * 2 + quiet_zone * 2)) + "\x1b[0m\n")
for r in range(modcount):
    out.write("\x1b[1;47m" + (" " * quiet_zone) + "\x1b[40m")
    for c in range(modcount):
        if self.modules[r][c]:
            out.write("  ")
        else:
            out.write("\x1b[1;47m  \x1b[40m")
    out.write("\x1b[1;47m" + (" " * quiet_zone) + "\x1b[0m\n")
out.write("\x1b[1;47m" + (" " * (modcount * 2 + quiet_zone * 2)) + "\x1b[0m\n")
out.flush()
```

**修复验证**

- 修复前：TC-C-011 失败，`assert 46 == 58`（见 `evidence-before-fix.txt`）。
- 修复后：TC-C-011 通过——行可见宽度 = 58；全部 12 条用例通过（见 `evidence-after-fix.txt`）。
- 修复仅改动 `print_tty` 的静区宽度计算，不改变任何模块像素与颜色逻辑，对
  `print_ascii`/`make_image`/图像后端无影响，风险可控。

**交叉复现**

按分工应由成员B独立复现：在修复前版本执行
`python -m pytest tests/manual -k tc_c_011`，应得到 `assert 46 == 58` 失败；
复现记录待成员B签字补充。

---

## 有效性说明

- 本缺陷有确定的错误行为（静区宽度与配置不符）、最小复现与代码级根因，
  修复后行为回归到与 `print_ascii` 一致并满足 QR 规范；
- 非"正常抛出的异常"：`print_tty` 不报错，而是输出错误宽度的静区，
  属"本应遵循配置却忽略配置"的静默错误；
- 修复补丁只改动 `main.py` `print_tty` 共 6 行，不影响合法输入下的输出像素。
