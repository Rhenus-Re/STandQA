# STandQA - python-qrcode 软件测试与质量保证实践

本仓库用于华中科技大学软件学院《软件测试与质量保证实践》小组作业。被测对象选定为 [lincolnloop/python-qrcode](https://github.com/lincolnloop/python-qrcode)，计划固定在 `8.2` 版本开展测试。

> 已引入 `python-qrcode v8.2` 被测源码；课程测试用例和测试脚本尚未加入。

## 1. 项目目标

本项目分为两个相互隔离的阶段：

- **模块一：测试基础实践**

  由小组成员人工完成需求分析、测试用例设计、自动化测试、缺陷定位与修复验证。本阶段不得使用 AI 生成测试用例或开展自动化测试。
- **模块二：AI 融合实践（AI 测）**

  在模块一冻结版本的基础上，使用 AI 辅助生成新增测试用例、测试数据和测试脚本，并记录 AI 辅助定位与修复缺陷的完整过程。

模块二的 AI 测试不得覆盖或改写模块一成果；两个阶段分别存放、分别统计、分别提交。

## 2. 被测范围

为控制代码规模，本项目不计划覆盖 `python-qrcode` 的所有样式扩展，主要测试以下三部分：

1. **编码与容量**：数据编码模式、版本选择、容量计算、纠错块与掩码。
2. **QRCode 对象行为**：参数检查、数据添加、自动适配、生成、清空、重复使用和异常行为。
3. **输出行为**：PNG、PyPNG、ASCII、必要的 SVG 输出以及命令行入口。

主要参考源码范围：

- `qrcode/main.py`
- `qrcode/util.py`
- `qrcode/base.py`
- `qrcode/image/`
- `qrcode/console_scripts.py`

## 3. 仓库结构

```text
STandQA/
├── qrcode/                         # python-qrcode v8.2 被测源码
│   ├── image/                      # PNG、SVG及样式化图像后端
│   ├── README.md                   # 上游版本与导入范围说明
│   └── LICENSE                     # 上游 BSD-3-Clause 许可证
├── tests/
│   ├── manual/                     # 模块一：人工设计的自动化测试
│   │   └── README.md
│   └── ai_generated/               # 模块二：AI生成且经人工审核的测试
│       └── README.md
├── testdata/
│   ├── manual/                     # 模块一人工准备的数据
│   │   └── README.md
│   └── ai_generated/               # 模块二AI生成且经审核的数据
│       └── README.md
├── reports/
│   ├── module1/                    # 模块一用例、缺陷、报告、PPT和结果
│   │   └── README.md
│   └── module2/                    # 模块二用例、缺陷、报告、PPT和结果
│       └── README.md
├── ai_records/                     # 模块二关键AI对话与审核记录
│   └── README.md
├── docs/
│   └── project-organization.md     # 阶段安排、分工和协作规则
├── .gitignore
├── requirements-test.txt           # 测试环境依赖；不包含被测源码
└── README.md
```

各目录内的 `README.md` 用于说明准入规则和文件命名方式，避免两个模块的成果混放。

## 4. 阶段交付目标

### 模块一

- 人工设计不少于 30 条测试用例，项目内部目标为 36 条。
- 覆盖等价类、边界值、场景法中的至少两种方法。
- 使用 `pytest` 实现一键运行。
- 记录并验证不少于 3 个有效缺陷，内部目标为 4 个。
- 提交测试用例清单、缺陷清单、测试报告、PPT和演示视频。
- 完成后创建 `module1-final` 标签，冻结模块一成果。

### 模块二

- 从 `module1-final` 创建 `module2-ai-testing` 分支。
- AI 生成不少于 15 条有效新增用例，项目内部目标为 18 条。
- 保存提示词、AI 原始输出、人工审核结论及修改记录。
- 使用 AI 辅助生成测试数据或脚本、定位缺陷并提出修复建议。
- 人工确认并验证不少于 1 个有效缺陷。
- 对比人工测试和 AI 测试的有效率、重复率、覆盖率增量、缺陷发现率和耗时。

## 5. 模块一三人分工

以下分工仅适用于模块一。详细职责见 [项目组织说明](docs/project-organization.md)。

| 成员 | 贡献度建议 | 模块一独立测试域 | 主要源码与方法 |
|---|---:|---|---|
| 成员 A／组长 | 34% | **编码与纠错**：编码模式、数据分段、位流、容量边界、RS 纠错、掩码公式与评分 | `util.py`、`base.py`、`LUT.py`、`constants.py` |
| 成员 B | 33% | **对象与矩阵**：参数校验、数据添加与清空、对象复用、版本适配、图案放置、掩码选择、矩阵生成 | `main.py`（输出方法除外）、`exceptions.py` |
| 成员 C | 33% | **输出与命令行**：PNG、PyPNG、SVG、ASCII、文件流、保存行为和 CLI 参数 | `image/base.py`、`image/pil.py`、`image/pure.py`、`image/svg.py`、`compat/*`、`console_scripts.py`，以及 `main.py` 的输出方法 |

三个测试域不得重复设计同一功能点。跨文件调用的用例按“主要断言对象”归属：验证编码、纠错或掩码评分结果归 A；验证 `QRCode` 对象状态、掩码选择或矩阵结果归 B；验证最终图像、文本、文件或 CLI 输出归 C。每名成员在自己的测试域内人工设计并实现 12 条用例、至少负责 1 个有效缺陷，并完成对应证据材料。缺陷交叉复现顺序为：A 发现的缺陷由 C 复现，B 发现的缺陷由 A 复现，C 发现的缺陷由 B 复现。

为控制模块一规模，暂不测试 `image/styledpil.py`、`image/styles/*`、`release.py` 及发布流程。

公共事务也分别指定主责：A 负责测试环境、覆盖率汇总、README和仓库整合；B 负责缺陷清单、根因分析和测试报告相关章节；C 负责用例清单、PPT和演示视频整合。每位成员须使用个人账号提交，任何成员不得代替他人提交。

模块二的人员分工不在本表中预设，将在 `module1-final` 冻结后根据模块一结果另行制定。

## 6. 分支与版本规则

- `main`：可展示、可提交的稳定成果。
- `module1-work`：模块一集成分支。
- `module2-ai-testing`：模块二 AI 测试分支，只能在 `module1-final` 之后创建。
- `member-a/*`、`member-b/*`、`member-c/*`：成员个人工作分支。
- `module1-final`：模块一提交快照标签。
- `module2-final`：模块二最终提交快照标签。

推荐提交信息：

```text
docs: 完善被测范围说明
test: 添加二维码容量边界测试
fix: 修复二维码对象清空后的状态问题
report: 补充模块一缺陷验证结果
ai-test: 添加经审核的AI生成测试
```

## 7. 环境与运行方式

计划环境：

- Python 3.10 或更高版本
- python-qrcode 8.2 源码
- pytest
- pytest-cov
- Pillow
- PyPNG

安装测试依赖：

```powershell
python -m pip install -r requirements-test.txt
```

在测试代码加入后，一键运行全部测试：

```powershell
python -m pytest
```

分别运行两个阶段的测试：

```powershell
python -m pytest tests/manual
python -m pytest tests/ai_generated
```

当前仓库已包含被测源码，但尚无课程测试代码，因此以上测试入口将在后续阶段启用。

## 8. 质量与审查要求

- 用例必须具有明确需求依据和可验证的预期结果。
- GitHub Issue、功能建议、正常抛出的异常不能直接视为有效缺陷。
- 缺陷发现者不能单独确认自己的缺陷，至少由另一名成员复现。
- 模块二 AI 输出必须经过人工审核，不得把 AI 推测直接作为缺陷结论。
- 提交前检查仓库中不得包含 API 密钥、账号、个人敏感信息或未脱敏对话。
- 报告中的个人贡献必须与 Git 提交记录一致。

## 9. 上游项目与许可

- 上游项目：[lincolnloop/python-qrcode](https://github.com/lincolnloop/python-qrcode)
- 固定测试标签：`v8.2`
- 上游 commit：`3704f57a1107dbf553a50f5b531da3859abe19cf`
- 上游许可：BSD-3-Clause

源码目录中保留了上游版权和许可证文件。为避免与课程模块一、模块二测试混淆，本次未导入上游项目自带的 `qrcode/tests/`。
