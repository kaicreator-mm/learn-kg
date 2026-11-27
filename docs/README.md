# Learn-KG v0.1.0 文档索引

状态：DRAFT，D014文本优先；R3待审，分类未冻结。历史HSK私有staging已备份及可读归档，非正式发布。
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
- [历史RDF首批实际导入证据](implementation/hsk-import-r2.md)
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
- [实施与证据合同](implementation/task-execution-contract.md) / [CQ覆盖账本](implementation/coverage-ledger.json)。审核前限制见 #6；历史D013以SQLite为候选实施基线；D014更新为文本优先，RDF仅保全与转换输入。

## D014 文本优先
- [可读知识包与SQLite导入合同](design/text-knowledge-package.md) / [原创结构样例](drafts/text-package-example/records.json)。D014草案，版本待审HEAD不变，当前不生成SQLite文件。

## 历史证据与文档补齐
- [当前建设事实与缺口](implementation/documentation-baseline.md)
- [SRC01 保全与可读归档](implementation/src01-readable-archive.md) / [机器可读证据](implementation/src01-preservation-evidence.json)
- [S01结构库存](drafts/s01-scope-inventory.json) / [来源调查](drafts/s01-source-calibration.md) / [DB01导入映射](drafts/db01-sqlite-design.md)

## S01 基础四域逐主题研究需求（调查草案）
- [K01–K04 范围细化与来源核验](drafts/s01/README.md)；不代表D4知识完成或G01通过。

- [S01 K01–K08累计细化](drafts/s01/README.md)，研究需求累计 197 / 648 D3（非知识完成率）。

- [S01 K01–K12累计细化](drafts/s01/README.md)；[测量、估计、决策与任务边界](drafts/s01/measurement-decision-boundary.md)，研究需求累计 313 / 648 D3（非知识完成率）。

- [S01 通用19域475主题需求全覆盖](drafts/s01/README.md)；[环境、学科、证据与治理组合边界](drafts/s01/context-evidence-governance-boundary.md)（调查草案，未完成专业资格）。

- [S01 通用/汉语26域648主题需求全覆盖](drafts/s01/README.md)；[HSK源归档与专业需求映射](drafts/s01/hsk-source-domain-mapping.md)（调查草案，未完成专业资格）。

- [S01 P/F/A/E 27视图研究需求](drafts/s01/process-view-requirements.md)；[CQ/LC正负夹具设计](drafts/s01/cq-lifecycle-fixture-requirements.json)（NOT_RUN）。

- [DB01/S01 BKT 原子知识与格式试点](drafts/db01-bkt-pilot/README.md)（调查草案，非正式专业资格）。

- [HLR与复习决策调查试点](drafts/db01-hlr-pilot/README.md)（专业候选与条件规则验证，不是正式模块资格）。

- [DB01 统一可读知识表达调查原型](drafts/db01-unified-pilot/README.md)（保留历史试点，未冻结正式schema）。

- [DB01 统一格式语言实体与有界活动扩展](drafts/db01-unified-pilot/README.md)（调查原型）。

- [K01 全19主题首轮实际专业内容调查稿](drafts/s01/K01/README.md)（D4候选、源定位与四视角案例，非正式K01完成收据）。

- [K02 全28主题首轮专业内容调查稿](drafts/s01/K02/README.md)（D4候选、证据、四视角及有限算术）。

- [K03 全26主题首轮专业内容调查稿](drafts/s01/K03/README.md)（原子候选、跨主题锚点及有限逻辑验证）。

- [K04 全24主题首轮专业内容调查稿](drafts/s01/K04/README.md)（技能、迁移及合成验证）。
