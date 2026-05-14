# Iteration 00 - Project Setup And Research Scaffold

日期：2026-05-12

## 迭代目标

建立 B 题项目的可复现工作环境、目录结构、资料登记机制、参赛单位结构化表和后续最优迭代主 Prompt。

## 新增数据或文献

- 从 `2026problem.pdf` 提取题面文本到 `docs/research/problem_text_extracted.txt`。
- 结构化 B 题 64 个参赛单位到 `data/raw/teams_from_problem.csv`。
- 下载 2024 浙江统计年鉴相关表：
  - `data/raw/zhejiang_statistical_yearbook_2024/17-25.html`
  - `data/raw/zhejiang_statistical_yearbook_2024/17-26.html`
- 解析年鉴 JS JSON 数据：
  - `data/processed/yearbook/17-25.csv`
  - `data/processed/yearbook/17-26.csv`
- 建立资料登记表：`docs/research/source_register.md`。

## 环境变化

用户要求不要继续修复 `base`，改为创建专用 conda 环境。

创建环境：

```powershell
conda create -y -n zju_math_model python=3.11 pip
```

安装依赖：

```powershell
conda run -n zju_math_model python -m pip install "numpy==1.26.4" pandas scipy scikit-learn matplotlib seaborn openpyxl html5lib lxml beautifulsoup4 requests PyMuPDF pypdf geopy folium pulp networkx tqdm pyarrow jupyter ipykernel ortools
```

验证结果：

```text
numpy 1.26.4
pandas 3.0.3
scipy 1.17.1
sklearn 1.8.0
pulp 3.3.1
ortools 9.14.6206
cp_model OK
```

Jupyter kernel：

```powershell
conda run -n zju_math_model python -m ipykernel install --user --name zju_math_model --display-name "Python (zju_math_model)"
```

依赖清单：

- `requirements-zju_math_model.txt`

## 模型或算法变化

本轮尚未求解分组；先完成数学框架：

- `docs/modeling/problem_formalization.md`
- 硬约束、软指标、抽签模型、场地选址模型和最优性判据。

## 关键参数

- Python 环境：`D:\Anaconda\envs\zju_math_model\python.exe`
- 参赛单位：64
- 市级队：11
- 县级队：53，其中县级市 20、县 32、自治县 1
- 小组数：16
- 每组队伍：4
- 承办地：8，每地 2 组

## 运行命令

```powershell
D:\Anaconda\envs\zju_math_model\python.exe src\extract_yearbook_json.py data\raw\zhejiang_statistical_yearbook_2024\17-25.html data\raw\zhejiang_statistical_yearbook_2024\17-26.html
```

输出：

```text
17-25: 90 rows, 16 columns -> data\processed\yearbook\17-25.csv
17-26: 90 rows, 5 columns -> data\processed\yearbook\17-26.csv
```

## 结果摘要

- 项目规则已写入 `agent.md`。
- 专用环境可用，避免继续污染 `base`。
- 题面参赛单位已结构化并通过数量校验。
- 官方年鉴表已下载和解析。
- 主 Prompt 已写入 `docs/prompts/master_prompt.md`。

## 与上一轮比较

这是初始迭代，无上一轮结果。

## 失败、风险和下一步

失败/风险：

- `conda run` 在 Windows GBK 控制台输出中文表格时可能报 UnicodeEncodeError；后续脚本优先直接调用 `D:\Anaconda\envs\zju_math_model\python.exe`。
- 年鉴表为 2023 数据，若找到 2024 或 2025 县级公开数据，应替换或做对比。
- 场馆数据尚未结构化。
- 球队真实实力数据缺失，初期只能用代理指标。

下一步：

1. 建立 `src` 中的队伍数据加载、硬约束检查和评价指标模块。
2. 用经纬度或地图 API 构造距离矩阵。
3. 建立第一版 CP-SAT/ILP 分组模型。
4. 生成 baseline 可行分组，并保存到 `experiments/iter01/`。
