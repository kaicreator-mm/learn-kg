# 动态学习过程声明式契约（D011 候选）
## 数据职责
通用学习科学知识库保存理论/机制/命题及模式和策略依据；过程知识包保存可复用活动模板、流程、反馈和激励策略、评价、适用性条件及案例；学科包保存事实、技能目标、资源与类型绑定；组合包保存显式跨域模板绑定及案例；xLearn 管理会话、学习者状态、真实观测、计划和授权执行。允许同一 SQLite 文件内多个逻辑模块或按需独立过程包；具体物理切分待DB01验证，不重复存储学科实体或每词每策略关系。
 
## 候选逻辑表（不冻结）
process_modes, activity_templates, process_templates, process_steps, process_transitions, process_bindings, feedback_policies, motivation_policies, assessment_policies, adaptation_policies, condition_specs, process_evidence, process_cases, process_validations.
每个模板/策略有 stable_id/version/status/owner；关联证据Claim、兼容能力与类型、角色、约束、输入输出契约；转移含来源/目标、事件、守卫、优先顺序或显式冲突处理、缺失/未知分支、重试预算、终止和可恢复检查点。
流程图允许有界循环，不应强制DAG；单次执行的因果事件记录可按时序形成有向无环追溯。条件只使用声明式受限表达式或已验证的函数引用，禁止任意数据库脚本执行。组合时校验版本依赖与稳定ID、直接依赖及能力兼容，缺失时拒绝或明确降级。
 
## 最小运行合同
Input: goal_ref, subject_scope, knowledge_or_skill_type, context, prior_observation_ref, learner_state_summary, time_budget, allowed_modalities, preferences/consent.
Output: next_activity / feedback / motivation_support / assessment_request / deferred_review / stop / need_clarification, reason + referenced knowledge/strategy/version.
实际观测不可被生成内容覆盖；评分和状态估计有独立 provenance。不得把题目正确自动等同掌握；不可因时间耗尽强行晋升；模型不确定不伪造状态；个体数据留在xLearn。
 
## 运行验证与边界
执行器与知识库分离，实际执行时只加载目标学科、所需通用机制/过程模板以及对应学习者记录；局部类型规则按需匹配。模板本身不是运行实例、不是固定教学最优证明。模板可版本化且历史会话绑定精确版本；升级不悄悄改变过去记录。失败、取消、暂停恢复、预算和重复事件需测试；不得使用无限重试或强制激励。DB01后续需落实schema与独立负例，当前无实际过程引擎或模拟结果。

## D012 组合扩展
输入需支持明确目标及成功证据、学习对象粒度、可用资源与交互能力、角色/授权、环境约束、个体自述与模型估计的分离；输出需支持独立任务证据、补救理由、下一步、迁移及学习者控制。跨次会话绑定精确知识/过程版本。外部改进只输出证据和候选变更，由独立审核及版本门禁决定是否发布，不能作为个体状态更新的同一写入路径。详见 [生命周期组合与数据契约](learning-lifecycle-contract.md)。
