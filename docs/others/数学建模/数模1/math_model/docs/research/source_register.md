# B 题资料登记表

访问日期：2026-05-12

## 题面与本地资料

1. 浙江大学第二十四届大学生数学建模竞赛试题，`2026problem.pdf`。
   - 用途：B 题硬约束、参赛单位、论文与 AI 使用说明要求。
   - 已提取文本：`docs/research/problem_text_extracted.txt`。
   - 已结构化参赛单位：`data/raw/teams_from_problem.csv`。

## 官方统计与行政资料

2. 浙江省统计局，2024 年浙江统计年鉴，https://tjj.zj.gov.cn/art/2024/12/2/art_1525563_58962725.html
   - 用途：县市人口、GDP、财政、消费、居民收入等代理指标。
   - 已下载原始表：`data/raw/zhejiang_statistical_yearbook_2024/17-25.html`、`17-26.html`。
   - 已解析表：`data/processed/yearbook/17-25.csv`、`17-26.csv`。

3. 浙江省统计局，2024 年浙江省国民经济和社会发展统计公报，https://tjj.zj.gov.cn/art/2025/3/1/art_1229129205_5469690.html
   - 用途：省级宏观背景、赛事影响力与城市发展指标的解释依据。

4. 国家统计局，统计用区划和城乡划分代码，https://www.stats.gov.cn/sj/tjbz/tjyqhdmhcxhfdm/
   - 用途：校验浙江省县级行政单元名称、行政层级和编码。

5. 中华人民共和国民政部，行政区划代码，https://www.mca.gov.cn/mzsj/xzqh/2023/202301xzqh.html
   - 用途：行政区划代码交叉验证；若 2025 版公开页可用，后续迭代改用最新版本。

## 地理与交通数据

6. OpenStreetMap Nominatim Usage Policy，https://operations.osmfoundation.org/policies/nominatim/
   - 用途：若使用 Nominatim 获取县市中心坐标，需遵守访问频率和标识要求。

7. GeoNames geographical database，https://www.geonames.org/
   - 用途：备选经纬度来源，用于构造球面距离矩阵；需核对行政单元命名。

8. 高德/百度/腾讯地图开放平台路径规划 API。
   - 用途：若队伍能申请 key，可用真实公路时间替代球面距离；未申请时用球面距离加敏感性分析。

## 体育场地与承办地资料

9. 国家体育总局，2024 年全国体育场地统计调查数据，https://www.sport.gov.cn/
   - 用途：体育场地总量、足球场地背景；后续应补充浙江省分市县数据或官方年鉴表。

10. 浙江省体育局官网，https://tyj.zj.gov.cn/
    - 用途：查找浙江省体育场地统计、重点体育场馆、足球赛事承办能力。

11. 各市县政府/体育局/场馆官网。
    - 用途：候选承办地的体育场容量、交通位置、承办经验；须在后续迭代逐项登记。

## 运筹优化、赛事公平与抽签文献

12. Guyon, J. Rethinking the FIFA World Cup final draw. Journal of Quantitative Analysis in Sports, 11(3):169-182, 2015. https://ideas.repec.org/a/bpj/jqsprt/v11y2015i3p169-182n1.html
    - 用途：约束抽签、公平性、分档与透明随机程序设计。

13. Rasmussen, R. V.; Trick, M. A. Round robin scheduling - a survey. European Journal of Operational Research, 188(3):617-636, 2008. https://doi.org/10.1016/j.ejor.2007.05.046
    - 用途：单循环赛程、主客/旅行/公平约束的运筹背景。

14. Kendall, G.; Knust, S.; Ribeiro, C. C.; Urrutia, S. Scheduling in sports: An annotated bibliography. Computers & Operations Research, 37(1):1-19, 2010. https://doi.org/10.1016/j.cor.2009.05.013
    - 用途：体育赛程优化方法综述与参考文献入口。

15. Osicka, O.; Guajardo, M. Fair travel distances in round-robin tournaments with a focus on the non-decreasing travels objective. European Journal of Operational Research, 2023. https://doi.org/10.1016/j.ejor.2022.10.030
    - 用途：旅行公平指标，支持场地选择与赛程建议。

16. Hakimi, S. L. Optimum locations of switching centers and the absolute centers and medians of a graph. Operations Research, 12(3):450-459, 1964.
    - 用途：p-median / p-center 设施选址理论源头，支持 8 个承办地选择模型。

17. Karp, R. M. Reducibility among combinatorial problems. In Complexity of Computer Computations, 1972.
    - 用途：说明组合优化问题复杂性，解释为何需要精确求解、启发式与敏感性分析结合。

## 后续资料缺口

- 最新县市 GDP/人口若能取得 2024 或 2025 公开县级表，应替换 2023 年鉴数据。
- 候选足球场馆容量、草坪类型、交通枢纽距离和承办经验需要逐项查证。
- 球队真实实力数据缺失，应明确用代理指标并做权重敏感性分析。
- 若使用地图 API 路径时间，需记录 key 来源、请求日期、字段和缓存文件。
