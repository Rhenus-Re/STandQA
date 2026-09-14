# 模块一 成员C 测试用例清单——输出与命令行域

被测版本：python-qrcode v8.2（commit `3704f57`）。共 12 条用例，覆盖等价类、
边界值、场景法三种方法。实现文件：`tests/manual/test_output_cli.py`。
一键运行：`python -m pytest`（在 `D:\tests\module1-test` 下）。

| 用例编号 | 设计方法 | 断言对象 | 需求依据 | 预期结果 | 结果 |
|---|---|---|---|---|---|
| TC-C-001 | 等价类 | PilImage 几何与模式 | 2.1 / 2.2 | width=21, pixel_size=290, mode="1", fill_color=0 | 通过 |
| TC-C-002 | 边界值 | PilImage 最小参数像素 | 2.1 / 2.2 | box_size=1/border=0：21×21，定位眼黑、定时图案交替 | 通过 |
| TC-C-003 | 场景法 | PilImage PNG 端到端 | 2.2 | 流/路径保存均产出合法 PNG，可重开、尺寸 290×290 | 通过 |
| TC-C-004 | 等价类 | PilImage 颜色三分支 | 2.2 | 默认"1"/透明 RGBA alpha=0/自定义 RGB 像素正确 | 通过 |
| TC-C-005 | 场景法 | PyPNG 端到端与跨后端一致 | 2.2 | 1 位灰度 PNG 290×290，静区白、定位眼黑，与 PIL 一致 | 通过 |
| TC-C-006 | 等价类 | PyPNG kind 校验与流/路径 | 2.2 | JPEG 拒绝且流空；PNG/默认合法；路径分支合法 | 通过 |
| TC-C-007 | 等价类 | SvgImage 根元素与命名空间 | 2.3 | 根 svg、xmlns、width/height=29mm；SvgFill 含白 rect | 通过 |
| TC-C-008 | 场景法 | SvgPathImage path 合并 | 2.3 | needs_processing=True，单一 path，d 非空，fill=#000000 | 通过 |
| TC-C-009 | 边界值 | print_ascii invert 与 border=0 | 2.4 | 11 行、每行 21 字符；invert 输出与非 invert 不同 | 通过 |
| TC-C-010 | 等价类 | tty 守卫 | 2.4 | print_ascii(tty=True)/print_tty 于非 tty 抛 OSError | 通过 |
| TC-C-011 | 场景法 | print_tty 静区遵循 border（C-BUG-01 回归） | 2.4 | 行可见宽度=58（modcount*2+border*4） | 通过（修复后） |
| TC-C-012 | 场景法 | CLI main 端到端 | 2.5 | --output PNG 合法；--factory svg SVG 合法；--ascii 15 行 | 通过 |

## 设计方法分布

| 方法 | 用例 | 数量 |
|---|---|---|
| 等价类 | TC-C-001 / 004 / 006 / 007 / 010 | 5 |
| 边界值 | TC-C-002 / 009 | 2 |
| 场景法 | TC-C-003 / 005 / 008 / 011 / 012 | 5 |

三种方法均覆盖（硬性指标要求 ≥ 2 种）。

## 执行结果汇总

- 用例总数：12
- 通过：12（修复后）
- 失败：0
- 失败率（修复前）：1/12 = 8.3%（仅 TC-C-011，对应 C-BUG-01）
- 通过率（修复后）：100%
- 发现有效缺陷：1（C-BUG-01）
