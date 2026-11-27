# F03/F04/F05/F07/A07/E01 受限流程组合候选与整改

状态：PREPARATION_ONLY；当前 remediation 分支尚未合并 version/v0.1.0，没有新候选资格收据或正式资格收据。

## 当前候选快照

- Package：learning-process@0.1.0-process-candidate-3
- 迁移：P01–P10 共 1,312 条记录，迁移差异仅为同包内部引用版本重绑定；本轮没有改动 P01–P10 专业记录。
- 新增：F03 38、F04 45、F05 33、F07 43、A07 68、E01 45 条 canonical records；合计 272 条。F/E 整改设计单独保存在 remediation-design.json，A07 原设计文件与记录字节保持不变。
- 总计：1,584 条记录。
- 有限案例：F03 12、F04 18、F05 11、F07 14、E01 16，共 71 项；A07 另有 26 项，本次独立审核明确不覆盖 A07。
- 构建回放：97 项 SQL builder-only cases（包含 A07 的 26 项）；37 项导入器既有单元测试和 19 项新增语义边界单元测试。均不是独立专业 oracle、CQ/LC 或真实学习者证据。

## 本轮独立审核与整改

Issue #10 的 F03/F04/F05/F07/E01 独立审核结论为 REWORK_REQUIRED：P0=0、P1=1、P2=4、P3=1。六项有限整改已写入本候选分支，新的精确 SHA 尚待提交后建立独立增量审核。

### F03 — 资源与表达

- 严格白名单：TEXT→READING、AUDIO→LISTENING、VISUAL→VISUAL_RECOGNITION。
- 未知/缺失模态或构念保持 HOLD；已知但错配返回 REJECT_CONSTRUCT_SUBSTITUTION。
- VISUAL 额外要求 visual_accessibility_verified=true；三条正向映射分别具有明确有限条件。
- PUBLIC_AUTHORIZED 正例仍是无实际媒体字节的合成描述，不代表真实资源权利或发布许可。

### F04 — 学习交互

- 首次响应、提示事件、最终响应、独立复测均为独立追加事件，包含稳定事件 ID、任务/版本/变式、发生时间、记录时间和学习者响应。
- 独立复测必须是新变式、独立响应、generated_answer=false、assistance_status=NONE，并绑定 F04.OBS.RETEST、原目标构念和 P06.ACT.OBSERVE.OBS 评分观察合同。
- 事件 SHA256 只验证候选事件对象的确定性完整性，不验证真实主体身份或签名。相同提示事件 ID/内容幂等，冲突 HOLD；缺少复测或生成答案来源未知不得晋升。
- 提示后的初始/最终响应不污染一个独立、无辅助的新变式复测；两者仍分别保留。

### F05 — 学习者状态

- 显式要求 expected_scoring_version，观察评分版本必须精确匹配；缺失预期版本、空版本或非空错误版本均 HOLD。
- 缺失/无效/未施测继续保持 UNKNOWN；模型估计与其它证据通道分离，estimator_ref=null，不推断综合掌握。

### F07 — 环境与角色

- 审核者角色明确只读并拒绝学习者支持建议；exit 必须精确为 false 才能继续，true 为 STOP，缺失/未知为 CLARIFY。
- 学习者支持请求有稳定事件身份、本人选择和摘要；角色授权对象绑定 actor、learner、role、purpose、scope、session、issued/not-before/expiry、permission 和 facilitator assignment。
- 促进者必须绑定指定学习者、明确范围、用途、会话和有效期限；但当前没有可信促进者授权解析器，因此促进者路径一律 HOLD。环境配置另有 profile/version/测试时间和摘要。
- 这些 SHA256 是合成候选对象的完整性摘要，不是可信签名/身份认证；学习者自选路径仅建议不执行，促进者路径在可信解析器绑定前保持 HOLD。没有运行时权限执行器。

### E01 — 外部改进闭环

- 新增只读 analysis-plan.json，定义 population identity/inclusion/exclusion、allocation unit/method、intervention/comparator versions、primary outcome、28-day follow-up、ITT estimand、missingness/safety rules 和发布边界。
- E01.PROTOCOL 使用 DB01 canonical v1 现有字符串槽位保存规范 JSON，并在 provenance 精确绑定分析计划路径与 SHA256；不修改 DB01 schema。
- 审批与独立复核要求使用类型化外部证据身份（repository、issue/comment、artifact path/hash、subject/version、plan hash、decision、authority、有效期）；旧的 approved / protocol_frozen / independent_review caller booleans 不再被接受。
- 当前没有可信审批/独立复核解析器，也没有实际审批文件。即使输入携带结构化证据引用，观察数据分析仍保持 HOLD；模拟仅为 SIMULATION_ONLY_NOT_EFFECT，未验证分配仅为 DESCRIPTIVE_ONLY_NO_CAUSAL_ESTIMATE。禁止直接写正式知识或发布。

### P3-01

E01 design case list 已去重，并与 16 个实际 fixture 名称精确一致。

## 精确验证边界

- P01–P10：本次审核已独立通过 1,312 条迁移完整性，但没有审核其专业内容。所有 P01–P10 candidate-3 收据精确重绑定与迁移 delta review 仍待完成，不能据此登记 F/E 资格。
- F/E：71 项 builder cases；A07：26 项 builder cases，明确不属于 Issue #10 审核范围。SQL 回放包含 A07 仅表示结构性加载和 builder 重放，不构成 A07 语义审核。
- F04 的 nested typed binding：F04.OBS.RETEST + P06.ACT.OBSERVE.OBS；F03/F04/F05/F07/A07/E01 的六组静态跨模块绑定均不是运行时执行证据。
- 导入器 37/37 与本模块语义边界单元测试 18/18 通过，仅证明有限软件合同/边界。
- 不含真实学习者数据、真实实验结果、实际媒体字节或发布授权。

## 未完成事项

- 新 remediation exact HEAD 的 F/E 分批独立增量审核：NOT_RUN。
- A07 独立审核：NOT_RUN。
- P01–P10 candidate-3 exact tuple rebind 与 migration delta review：PENDING。
- SRC01 历史原始 PDF 身份/权利、G03/G04/G05、CQ/LC、专业覆盖充分性和发布资格：仍各自 HOLD/NOT_RUN。
- 无通用运行时、真实状态估计器、调度器、跨进程检查点、身份认证器、权限执行器或知识库写入器。
