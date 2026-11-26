# Learn-KG v0.1.0 文档索引

状态：DRAFT，分类未冻结、未完成独立审核；已建立 HSK 私有 staging 图，非正式发布。
- [领域范围及能力问题](product/knowledge-scope.md)
- [知识证据与案例合同](product/knowledge-quality-contract.md)
- [首批案例需求](product/case-pilot.md)
- [来源发现](research/source-discovery.md)
- [阶段建设计划](implementation/knowledge-graph-plan.md)
- [讨论决策记录](product/decision-index.md)

主线 #1，版本 #2，实施总控 #6（#3/#4/#5 并行）。以原始来源支撑专业事实，不以本项目提案作为专业证据。

- [HSK 学科知识域与组合验证计划](product/hsk-domain-pilot.md)

- [HSK 用户资料登记、原文初读及来源风险](research/hsk-source-intake.md)

## D009 知识体系先行（当前候选入口）
- [知识体系 R1](product/system/README.md)：通用19域、汉语7域及8类组合能力；D1–D3结构库存、非知识点验收。

## D010 并行图数据库与 HSK 导入
- [历史 RDF staging 设计（已由D013替代）](design/graph-database.md)
- [HSK01 首批实际导入证据](implementation/hsk-import-r2.md)
- [导入工具](../tools/hsk_import/README.md)
任务 #4 DB01、#5 HSK01 与 #3 G01 并行；staging 不等于 accepted。

## D011 动态学习过程知识（候选）
- [过程知识体系](product/system/learning-process-system.md)
- [过程契约与运行边界](design/learning-process-contract.md)
- [专业范围参考](research/learning-process-sources.md)

## D012 完整学习生命周期（已采纳范围，专业内容待深化）
- [八个补充体系、双闭环及十个逻辑子系统](product/system/learning-lifecycle-system.md)
- [生命周期组合与数据契约](design/learning-lifecycle-contract.md)
- [生命周期能力问题与验收矩阵](implementation/learning-lifecycle-acceptance.md)

## D013 实施总控
- [实施Task DAG](implementation/task-dag.md) / [机器可读JSON](implementation/task-dag.json)，总控 #6；#3/#4/#5并行复用。

## D013 R2 修正候选
- [实施与证据合同](implementation/task-execution-contract.md) / [CQ覆盖账本](implementation/coverage-ledger.json)。审核前限制见 #6；SQLite实施基线，历史RDF仅迁移与保全。

## D014 文本优先
- [可读知识包与SQLite导入合同](design/text-knowledge-package.md) / [原创结构样例](drafts/text-package-example/records.json)。D014草案，版本待审HEAD不变，当前不生成SQLite文件。
