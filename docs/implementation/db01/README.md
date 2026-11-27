# DB01 — 正式候选文本格式与导入映射
当前D014：UTF-8 Markdown解释、JSON记录和JSONL权威数据；不生成持久SQLite。基线 learn-kg-canonical-candidate-1 尚非G04冻结。原专业源记录仍为权威，按模块编写/明确迁移后才可消费正式包；不以示例、原始记录或schema通过判定事实资格。

- canonical.schema.json：39类记录及严格manifest；独立Source/Locator/Claim/Element/Relation/Case/Validation，数值模型/条件/策略，汉语字/读音/词/义项/构式/标准/源成员，目标/能力/知识技能类型/学习对象/资源/模态/角色/环境/观测/状态/活动/交互/任务/模式/流程/组合/评价。结构化表达禁止任意代码。
- mapping-contract.json：每类专业字段到确定性表列，复杂字段JSON编码且typed references另建索引；按包+版本+稳定ID+类型+owner绑定，本地FK、跨包显式manifest resolver、直接依赖、资格/权利/隔离；六个逻辑角色（包括未来学科）不是强制物理库数量。类型级策略优先，关系端点12类为初始明确支持集合；新增专业关系须版本化补充，不能默认同义或蕴涵。
- 版本manifest固定源文件hash/版本/依赖manifest hash及资格引用，拒绝路径越界、未知字段、错版本、错类型、私有/候选/个人越界。结构schema并不单独授予资格，DB02必须真实检查解析、hash、重复ID/键、权限和当前收据，内存SQLite逐类对账、FK、按需查询与EXPLAIN；实际文本激活/恢复另测，物理SQLite文件测试保持HOLD。
- build_contract.py 生成两个候选合同；verify_contract.py 对299个准确源文件及13分片进行有限实际适配，保留原文provenance指针，未另写重复权威知识文件。实际验证455 Source、995 Locator、1743 Claim（含3历史）、2625 Case（648原四视角拆分与33数值设计）、33 Validation，13276 typed refs，12个schema负例拒绝。原案例及字段保留，未覆盖全部39种实体实例/专业字段语义；后续IF01提供共享端点/组合约束，DB02正式导入，专业模块形成具体规范记录。第一次25秒验证超时，调整后实际完成，未宣称失败尝试通过。

本任务交付设计及有限结构见证，不是DB02运行验收、专业资格、CQ/LC或发布；不需要另做完整独立设计审核，随IF01和后续模块/G04审查实际合同。
