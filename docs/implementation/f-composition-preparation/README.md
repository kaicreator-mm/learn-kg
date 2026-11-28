# F03/F04/F05/F07/A07/E01 受限流程组合候选与整改

状态：PREPARATION_ONLY；当前 remediation 分支尚未合并 version/v0.1.0，没有新候选资格收据或正式资格收据。

## 当前候选快照

- Package：learning-process@0.1.0-process-candidate-3
- 迁移：P01–P10 共 1,312 条记录，迁移差异仅为同包内部引用版本重绑定；本轮没有改动 P01–P10 专业记录。
- 新增：F03 45、F04 59、F05 35、F07 50、A07 81、E01 54 条 canonical records；合计 324 条。
- 总计：1,636 条记录。
- 有限案例：F03 15、F04 25、F05 12、F07 17、E01 20，共 89 项；A07 另有 32 项，已独立审核并进入单独整改。
- 构建回放：121 项 SQL builder-only cases（包含 A07 的 32 项）；导入器单元测试 37/37、语义边界测试 29/29、27 个关键产物确定性重放一致、迁移/结构不变量及 IF01 有限接口验证通过。它们不是独立专业 oracle、CQ/LC 或真实学习者证据。

## 本轮独立审核与整改

原 Issue #10 的 F03/F04/F05/F07/E01 审核为 REWORK_REQUIRED；Issue #12–#14 对上轮整改又发现新问题。A07 Issue #15 另发现两项 P1 和两项 P2。当前提交将这些有限问题合并到一个新精确候选快照，但仍须按模块分批独立增量审核。

### F03 — 资源与表达

- 严格白名单：TEXT→READING、AUDIO→LISTENING、VISUAL→VISUAL_RECOGNITION。
- 未知/缺失模态或构念保持 HOLD；已知但错配返回 REJECT_CONSTRUCT_SUBSTITUTION。
- VISUAL 正例不再接受 caller boolean；必须绑定 F03.ACCESSIBILITY.VISUAL.V1，核对资源 identity/version、模态、目标构念、测试范围/结果及确定性摘要。
- 该对象是项目作者合成候选记录，不是实际媒体、真实测试报告或可信无障碍认证；真实资源/发布权利仍独立 HOLD。

### F04 — 学习交互

- 首次响应、提示事件、最终响应、独立复测均为独立追加事件。
- task/scoring version 必须非空并匹配固定版本；空字符串双边相等不再通过。
- event_time 和 recorded_at 都使用 UTC epoch seconds，记录 client/server clock identity、clock domain、bounded sync 和最大 300 秒 skew；recorded_at 按追加顺序单调不减，事件时间顺序单独验证。
- 独立复测必须是新变式、独立响应、generated_answer=false、assistance_status=NONE，并绑定 F04.OBS.RETEST、原目标构念和 P06.ACT.OBSERVE.OBS。
- 事件 SHA256 只验证候选事件对象完整性，不验证真实主体身份或时钟来源真实性。

### F05 — 学习者状态

- expected_scoring_version 必须精确等于组合合同固定的 S1；不能由 caller 同时把预期版本和实际版本改成 S2 来绕过。
- 缺失/无效/未施测继续保持 UNKNOWN；模型估计与其它证据通道分离，不推断综合掌握。

### F07 — 环境与角色

- 审核者只读；exit 必须精确为 false 才能继续；true 为 STOP，缺失/未知为 CLARIFY。
- 环境 profile 绑定任务/版本、测试时间、有效期和重算摘要；accessible 与 capability_match 任一不满足都 DEFER。
- 学习者本人和促进者授权均需要可信解析器。当前两个解析器都未绑定，相关路径保持 HOLD/REQUEST_OBSERVATION。
- 机器可读 PolicySpec 不再含有 SUGGEST 规则；不能绕过语义检查器，仅凭 caller booleans 和结构字段获得建议。
- SHA256 是对象完整性摘要，不是签名或身份认证；没有运行时权限执行器。

### A07 — 环境/发展/差异到支持

- exit 只有精确 false 才允许继续；缺失、null、未知一律 CLARIFY。
- A07 不再接受顶层 permission=true、support_request_verified=true 或 environment_profile_verified=true 代替证据；必须消费完整 F07 输入对象并调用 F07 有界决策。
- A07 composition 的 input_refs 与 condition_refs 直接绑定 F07 exit、reviewer、deny、unavailable、learner resolver、facilitator resolver 和 offer guards。
- 环境 profile 绑定 task/version、tested_at/valid_until、能力/可及性及重算 digest；过期、任务不匹配或摘要错误不通过。
- construct review 绑定 review ID/version、task/version、assessment ID/version、construct、relation、result、时间窗口和重算摘要。
- 当前 F07 trusted identity resolver 未绑定，故 A07 即使其余候选输入完整，也只能 REQUEST_OBSERVATION，不能 SUGGEST。所有输出仍是 ADVICE_ONLY；没有真实学习者或发展阶段评估。

### E01 — 外部改进闭环

- analysis-plan.json 逐字段投影到 DB01 canonical v1 的四个 JSON 字符串槽位；验证器检查 population、allocation、intervention、comparator、primary outcome、estimand、follow-up、uncertainty 和精确 provenance tuple。
- 审批与独立复核证据必须是不同 comment、artifact、digest 和 authority identity；检查 evaluation_time 有效区间、路径穿越、文件存在与实际 SHA256。
- CURRENT/CANDIDATE 机器策略都绑定完整证据字段与 direct_knowledge_write=false。
- 可信审批/独立复核 resolver 仍未绑定；候选 PolicySpec 不再包含 SUGGEST，只能 REQUEST_OBSERVATION。观察数据分析保持 HOLD；模拟仅为 SIMULATION_ONLY_NOT_EFFECT，未验证分配仅为 DESCRIPTIVE_ONLY_NO_CAUSAL_ESTIMATE。

## 精确验证边界

- P01–P10：1,312 条迁移记录的字段级版本重绑定保持不变；P01–P10 专业内容没有在本批重新审核。candidate-3 收据精确重绑定和 migration delta review 仍待完成。
- F/E：89 项有限 builder cases；A07：32 项 builder cases。121 项 SQL 回放仅是结构加载和 builder 重放，不构成独立专业 oracle。
- F04 的 nested typed binding：F04.OBS.RETEST + P06.ACT.OBSERVE.OBS；A07 直接绑定 F07 结构化 guards。静态引用不代表运行时授权器或流程执行。
- 合成事件/环境/构念审核对象的 SHA256 不证明来源真实性、真实学习者身份、版权或无障碍认证。
- 不含真实学习者数据、真实实验结果、实际媒体字节或发布授权。

## 未完成事项

- 新 remediation exact HEAD 的 F03/F04、F05/F07、E01、A07 分批独立增量审核：PENDING。
- F07 学习者/促进者可信授权解析器：NOT_BOUND；相关建议路径 HOLD。
- E01 审批/独立复核可信解析器：NOT_BOUND；观察数据分析 HOLD。
- P01–P10 candidate-3 exact tuple rebind 与 migration delta review：PENDING；P09 的 same-learner identity/time-unit 缺陷仍需单独整改。
- SRC01 已取得 ACCEPT_SCOPED / PRESERVATION_VERIFIED，但历史 PDF 身份、权利和视觉资格仍保留限制；HSK01/HS00/H01–H07 需按其各自任务推进。
- G03/G04/G05、CQ/LC、专业覆盖充分性和发布资格仍各自 HOLD/NOT_RUN。
- 无通用运行时、真实状态估计器、调度器、跨进程检查点、身份认证器、权限执行器或知识库写入器。

### Integrated P09 and candidate-3 tuple rebind (new snapshot)
Historical sections above describe the earlier reviewed candidate. New preparation candidate merges reviewed P09 #28 and F/E/A07 #17–20, #27 on the version baseline. The 1,401 P source records are migrated (1,232 exact internal ref-only transformations, 169 unchanged); 324 F/E/A07 records remain unchanged, total 1,725. Fifteen target canonical shards byte-identical to the prior accepted candidate-3; P09 updated only. All 360 current P cases and 143 inherited P cases replay against candidate-3 SQL via replay_p_rebind.py; 121 F/E/A07 cases separate. P07 exact canonical typed entry accepts a version only via the explicit finite replay configuration (default candidate-2; explicit candidate-3 allowed), not caller rule content; P09 no SUGGEST and wrapper unchanged. Serialized adversarial input strings remain unchanged. Historical reviews are not registrations for the new manifest. Current receipts/DAG unchanged until exact integrated independent review; no release, persistent SQLite, professional or rights promotion.
