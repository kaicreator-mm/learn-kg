# 知识证据与案例合同（L1候选，非最终图谱 schema）

## 知识链
Source → EvidenceLocator → Claim → Element/Relation → Case → Validation。
- Source：稳定 ID、题名、作者/机构、年份、版本、DOI/URL、访问与权利状态、研究设计。
- EvidenceLocator：精确章节/页/段/表/图/公式及可核验定位；原文与原创归纳区分。
- Claim：独立命题、类型（定义/理论假说/实证结果/数学模型/规范/工程策略）、条件、适用人群、材料、比较组、结果指标、时间窗口、限制、证据方向与争议。对量化结果保留单位、估计量及不确定性，缺失不编造。
- Element/Relation：稳定 ID、类型、主责域、定义、关系方向、条件、来源 claim、版本；区分 prerequisite_for、part_of、associated_with、supports、contradicts、causal_effect_under、estimated_by、observed_by、informs_decision。关系不自动可传递或可逆；因果须有适当识别证据。
- Case：明确目标 D4/Claim ID、输入、条件、推理步骤、预期输出、依据、反例、不可判定边界、验证方法。
- Validation：独立预期或原始参考、实际结果、复现方法、Exact HEAD、失败与限制。

## 状态分离
来源：DISCOVERED / LOCATED / QUALIFIED / RESTRICTED；主张：DRAFT / SUPPORTED / CONTESTED / HOLD / REJECTED / ACCEPTED_SCOPED；验证：NOT_RUN / PASS / FAIL / BLOCKED。状态分别记录，不能因来源可信而自动通过主张。只读摘要、书目或页面发现不等同原文资格。
 
## 双向与四视角案例
A 知识→结果：在明确条件下预测或计算；B 观察→知识：提出候选解释及区分证据，而非把结果当作唯一原因；C 目标→干预：比较策略与适用前提；D 反例/失效→拒答或改策。每个可执行规则有正/负/边界条件；非确定性问题允许多个解释或 UNKNOWN。需同时验证从原子可找到案例，以及由案例可定位准确原子与证据。真实学习效果、算法计算正确性、检索能力分别评估。
 
## 特别防错
- 正确率不等于掌握度，回忆概率不等于迁移能力，模型潜变量不等于观察事实。
- 学习过程中的高表现不自动代表长期学习；研究群体平均效应不自动代表个体最优。
- 相关不等于因果；学习者观测缺失不等于未掌握；不得把学习风格标签当作有效干预依据。
- 区分经验研究、数学推导与软件政策；算法实现、参数默认值与教育有效性分别举证。
- 数据、文献许可、个人隐私独立门禁；公开仓库不放私有产品资料或个人学习记录。
