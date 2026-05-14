# Codex 项目总结与交接文档

日期：2026-05-12

## 1. 当前任务理解

本项目是浙江大学第二十四届大学生数学建模竞赛 B 题“浙超”分组方案。题目要求不是简单随机分组，而是同时解决四类问题：

1. 64 支队伍分成 16 个 4 队小组，并满足行政隶属相关约束。
2. 设计公开、透明、可执行的抽签机制，使抽签结果满足约束并具有较好公平性。
3. 选择 8 个市或县作为小组赛承办地，每个地点承办 2 个小组。
4. 基于数学模型和定量分析提出赛制建议。

我对本项目的定位是：先建立可复现的研究与实验框架，再逐轮迭代算法，最终形成“组合优化模型 + 可审计抽签机制 + 设施选址模型 + 赛制建议”的完整论文主线。

## 2. 已完成内容

### 项目规范

已创建 `agent.md`，明确后续 agent 的执行规则：

- 所有迭代必须留下痕迹；
- 外部数据必须记录来源；
- 题面约束是硬约束；
- 外部统计、地理、场馆和文献数据只能作为软目标或论证依据；
- 最终方案必须经过硬约束检查、分项评价、多权重/多 seed 敏感性分析。

### Python 环境

用户决定不继续使用 `base`，改为创建专用环境：

```powershell
conda create -y -n zju_math_model python=3.11 pip
```

环境路径：

```text
D:\Anaconda\envs\zju_math_model
```

后续推荐运行命令：

```powershell
$env:PYTHONUTF8='1'
& 'D:\Anaconda\envs\zju_math_model\python.exe' <script.py>
```

已安装并验证的核心包：

- `numpy 1.26.4`
- `pandas 3.0.3`
- `scipy 1.17.1`
- `scikit-learn 1.8.0`
- `PuLP 3.3.1`
- `OR-Tools 9.14.6206`
- `PyMuPDF`
- `requests`
- `beautifulsoup4`
- `geopy`
- `folium`
- `networkx`
- `matplotlib`
- `seaborn`

依赖清单保存于 `requirements-zju_math_model.txt`。

### 题面与队伍数据

已从 `2026problem.pdf` 提取题面文本：

```text
docs/research/problem_text_extracted.txt
```

已将 B 题参赛单位结构化：

```text
data/raw/teams_from_problem.csv
```

校验结果：

- 总队伍数：64
- 市级队：11
- 县级队：53
- 县级队中县级市：20
- 县级队中县：32
- 县级队中自治县：1

注意：题面称“20 个县级市和 33 个县”，其中“景宁畲族自治县”在结构化表中单列为自治县；建模时仍归入县级队，总数与题面一致。

### 官方统计数据

已下载并解析浙江省统计局 2024 年浙江统计年鉴中的两张表：

```text
data/raw/zhejiang_statistical_yearbook_2024/17-25.html
data/raw/zhejiang_statistical_yearbook_2024/17-26.html
```

解析后的可用数据：

```text
data/processed/yearbook/17-25.csv
data/processed/yearbook/17-26.csv
```

含义：

- `17-25.csv`：各市、县国民经济主要指标，含人口、GDP、产业、消费、财政、收入等。
- `17-26.csv`：各市、县年末人口数。

解析脚本：

```text
src/extract_yearbook_json.py
```

说明：年鉴网页不是普通 HTML 表格，而是把表格数据存放在 `var data = {...}` 的 JSON 中，所以我写了专用解析脚本，保留原始 JSON 与 CSV。

### 资料与文献框架

已创建资料登记表：

```text
docs/research/source_register.md
```

已登记的资料类型包括：

- 题面 PDF；
- 浙江统计年鉴；
- 浙江统计公报；
- 国家统计局行政区划代码；
- 民政部行政区划代码；
- OpenStreetMap Nominatim；
- GeoNames；
- 体育场地统计；
- 体育赛程优化、抽签公平、旅行公平和设施选址相关文献。

### 数学建模框架

已创建：

```text
docs/modeling/problem_formalization.md
```

核心思路：

- 分组问题：0-1 整数规划或 CP-SAT。
- 行政约束：硬约束。
- 同市县级队回避：软约束优先最小化。
- 实力/影响力/地理距离：软目标。
- 抽签：分档 + 受限随机 + 在线可行性检查 + 蒙特卡洛审计。
- 场地：带容量约束的 p-median / p-center / facility location。
- 最优性：Pareto 前沿、多 seed、多权重敏感性、硬约束验证和 gap 证据。

### 主 Prompt

已创建后续迭代主 Prompt：

```text
docs/prompts/master_prompt.md
```

这个 Prompt 的作用是让任意后续 agent 或 AI 工具快速接手项目，继续执行“资料 -> 建模 -> 算法 -> 实验 -> 论文”的迭代。

### 迭代记录

已创建初始迭代日志：

```text
iterations/2026-05-12_iter00_project_setup.md
```

该日志记录了环境创建、依赖安装、数据下载、年鉴解析、文件结构和下一步任务。

## 3. 当前项目文件地图

```text
agent.md
README.md
requirements-zju_math_model.txt
2026problem.pdf
2026face.doc

data/
  raw/
    teams_from_problem.csv
    zhejiang_statistical_yearbook_2024/
  processed/
    yearbook/
      17-25.csv
      17-25.json
      17-26.csv
      17-26.json

docs/
  project_summary.md
  modeling/
    problem_formalization.md
  prompts/
    ai_usage_log.md
    master_prompt.md
  research/
    problem_text_extracted.txt
    research_brief.md
    source_register.md

iterations/
  2026-05-12_iter00_project_setup.md

src/
  extract_yearbook_json.py
```

## 4. 当前风险与注意事项

1. `base` 环境曾被安装包过程影响过，但后续项目已切换到独立环境 `zju_math_model`。
2. Windows PowerShell 默认 GBK 输出中文时可能乱码或触发 `conda run` 的 Unicode 错误，后续建议设置 `$env:PYTHONUTF8='1'` 并直接调用专用环境的 `python.exe`。
3. 年鉴数据目前是 2023 年县市数据。如果能找到 2024 或 2025 县级公开表，后续应替换或对比。
4. 球队真实实力数据尚缺，初期只能用人口、GDP、财政、消费、收入等构造代理指标。论文中必须说明代理假设并做敏感性分析。
5. 场馆和交通数据尚未结构化。承办地模型第一版可先用县市政府驻地经纬度，后续应升级为真实体育场馆与交通时间。

## 5. 建议下一轮迭代

下一轮建议命名为：

```text
iterations/2026-05-12_iter01_baseline_grouping.md
```

建议目标：

1. 写 `src/data_loader.py`：读取队伍表和年鉴表。
2. 写 `src/constraints.py`：实现硬约束检查器。
3. 写 `src/baseline_grouping.py`：生成第一版可行分组。
4. 写 `src/evaluate_grouping.py`：输出硬约束、同市县级队冲突、组内代理实力均衡等指标。
5. 保存结果到 `experiments/iter01/`。

第一版不追求最终最优，先确保：

- 可运行；
- 可复现；
- 分组结果能通过硬约束；
- 评价指标可自动输出；
- 迭代日志完整。

## 6. 给后续 agent 的一句话

不要急着“给答案”。这个题真正能拉开差距的是：把行政约束、抽签公平、地理旅行、影响力覆盖和赛制建议统一到一个可解释、可复现、可审计的优化框架里，然后用多轮实验说明为什么最终方案确实优于朴素分组。
