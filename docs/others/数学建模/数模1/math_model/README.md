# 浙江大学数学建模竞赛 B 题：“浙超”分组方案

本仓库用于完成浙江大学第二十四届大学生数学建模竞赛 B 题“浙超”分组方案。目标是通过可复现的数据、模型、代码和迭代记录，逐步形成高质量的分组方案、抽签机制、承办地选择方案和赛制建议。

## 项目目标

题目要求浙江省 64 个市县单位参加拟议中的“浙超”联赛：

- 第一阶段：16 个小组，每组 4 队，单循环；
- 小组前两名晋级；
- 第二阶段：32 强淘汰赛，5 轮决出冠军；
- 需要给出若干分组方案并比较优劣；
- 需要设计可行抽签方案；
- 需要选择 8 个小组赛承办地，每个地点承办 2 个小组；
- 需要基于数学模型和定量分析提出赛制建议。

本项目的核心思路是：

> 将“浙超”分组建模为带行政硬约束、多目标软偏好和可审计随机机制的组合优化问题，再将承办地选择建模为带容量约束的设施选址问题。

## 当前状态

已完成：

- 创建项目执行规范：`agent.md`
- 创建专用 conda 环境：`zju_math_model`
- 提取题面文本：`docs/research/problem_text_extracted.txt`
- 结构化 64 支参赛队伍：`data/raw/teams_from_problem.csv`
- 下载并解析浙江统计年鉴相关数据：
  - `data/processed/yearbook/17-25.csv`
  - `data/processed/yearbook/17-26.csv`
- 建立资料登记表：`docs/research/source_register.md`
- 建立数学形式化框架：`docs/modeling/problem_formalization.md`
- 建立后续迭代主 Prompt：`docs/prompts/master_prompt.md`
- 建立初始迭代日志：`iterations/2026-05-12_iter00_project_setup.md`

## 环境配置

本项目使用专用 conda 环境，不推荐继续使用 `base`。

环境路径：

```text
D:\Anaconda\envs\zju_math_model
```

创建环境：

```powershell
conda create -y -n zju_math_model python=3.11 pip
```

安装依赖：

```powershell
conda run -n zju_math_model python -m pip install "numpy==1.26.4" pandas scipy scikit-learn matplotlib seaborn openpyxl html5lib lxml beautifulsoup4 requests PyMuPDF pypdf geopy folium pulp networkx tqdm pyarrow jupyter ipykernel ortools
```

推荐运行方式：

```powershell
$env:PYTHONUTF8='1'
& 'D:\Anaconda\envs\zju_math_model\python.exe' src\extract_yearbook_json.py data\raw\zhejiang_statistical_yearbook_2024\17-25.html data\raw\zhejiang_statistical_yearbook_2024\17-26.html
```

依赖清单：

```text
requirements-zju_math_model.txt
```

## 目录结构

```text
.
├── agent.md
├── README.md
├── requirements-zju_math_model.txt
├── 2026problem.pdf
├── 2026face.doc
├── data/
│   ├── raw/
│   │   ├── teams_from_problem.csv
│   │   └── zhejiang_statistical_yearbook_2024/
│   └── processed/
│       └── yearbook/
│           ├── 17-25.csv
│           ├── 17-25.json
│           ├── 17-26.csv
│           └── 17-26.json
├── docs/
│   ├── project_summary.md
│   ├── modeling/
│   │   └── problem_formalization.md
│   ├── prompts/
│   │   ├── ai_usage_log.md
│   │   └── master_prompt.md
│   └── research/
│       ├── problem_text_extracted.txt
│       ├── research_brief.md
│       └── source_register.md
├── experiments/
├── iterations/
│   └── 2026-05-12_iter00_project_setup.md
├── output/
└── src/
    └── extract_yearbook_json.py
```

## 关键数据

### 题面队伍表

```text
data/raw/teams_from_problem.csv
```

字段：

- `team`：参赛单位名称；
- `team_level`：`city` 或 `county`；
- `parent_city`：所属或代管市；
- `admin_type`：副省级城市、地级市、县级市、县、自治县；
- `source`：来源。

校验：

- 总数：64
- 市级队：11
- 县级队：53

### 统计年鉴表

```text
data/processed/yearbook/17-25.csv
data/processed/yearbook/17-26.csv
```

用途：

- 构造实力代理指标；
- 构造城市影响力指标；
- 支持赛制建议中的定量分析；
- 后续结合经纬度和场馆数据做承办地选择。

## 建模方向

### 分组模型

建议使用 CP-SAT 或整数规划：

- 决策变量：`x[t,g]` 表示队伍 `t` 是否进入小组 `g`；
- 硬约束：
  - 每队恰好一个小组；
  - 每组恰好 4 队；
  - 市级队分配在不同小组；
  - 市级队不与其代管县级队同组；
- 软目标：
  - 同一市代管县级队尽量不同组；
  - 组间实力代理指标均衡；
  - 组间影响力均衡；
  - 地理分散和旅行负担合理；
  - 观赏性适度提升。

### 抽签模型

推荐“分档 + 受限随机 + 可行性检查 + 蒙特卡洛审计”：

- 抽签过程要能公开执行；
- 每次抽取后检查是否仍能扩展成完整可行分组；
- 用大量模拟估计队伍落组概率、两队同组概率和偏差。

### 承办地模型

建议使用带容量约束的设施选址模型：

- 选 8 个承办地；
- 每个承办地承办 2 个小组；
- 目标平衡总旅行距离、最大旅行距离、区域覆盖、承办能力和赛事影响力；
- 若场馆数据不足，第一版可用县市政府驻地作为近似点，后续替换为真实场馆。

## 运行校验

校验当前数据：

```powershell
$env:PYTHONUTF8='1'
& 'D:\Anaconda\envs\zju_math_model\python.exe' -c "import pandas as pd; teams=pd.read_csv('data/raw/teams_from_problem.csv'); econ=pd.read_csv('data/processed/yearbook/17-25.csv'); pop=pd.read_csv('data/processed/yearbook/17-26.csv'); assert len(teams)==64; assert (teams.team_level=='city').sum()==11; assert (teams.team_level=='county').sum()==53; assert len(econ)==90; assert len(pop)==90; print('validation OK')"
```

期望输出：

```text
validation OK
```

## 迭代规则

每一轮算法、数据或论文结构变化，都必须写入 `iterations/`。

建议文件名：

```text
YYYY-MM-DD_iterNN_<short-name>.md
```

每轮至少记录：

- 迭代目标；
- 新增数据或文献；
- 模型/算法变化；
- 参数和随机种子；
- 运行命令；
- 结果摘要；
- 与上一轮比较；
- 失败点、风险和下一步。

实验产物保存到：

```text
experiments/iterNN/
```

最终方案、图表和论文材料保存到：

```text
output/
```

## 推荐下一步

下一轮建议做 baseline 分组：

1. 创建 `src/data_loader.py`，统一读取队伍和年鉴数据。
2. 创建 `src/constraints.py`，实现硬约束检查器。
3. 创建 `src/baseline_grouping.py`，生成第一版可行分组。
4. 创建 `src/evaluate_grouping.py`，输出分项评价指标。
5. 保存结果到 `experiments/iter01/`。
6. 记录日志到 `iterations/2026-05-12_iter01_baseline_grouping.md`。

## 重要提醒

- 不要把人口、GDP 等代理指标说成真实球队实力。
- 不要只输出一个总分，必须输出分项指标。
- 不要只给一个方案，至少比较多个候选方案。
- 不要只说“随机抽签”，必须给出可公开执行的抽签流程和模拟审计。
- 不要声称全局最优，除非有求解器最优性证明或明确 gap；否则应表述为“当前数据和计算预算下的近优方案”。
