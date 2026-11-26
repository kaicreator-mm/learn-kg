# 生命周期组合与数据契约（D012 设计候选）
## 物理边界
SQLite多知识库隔离为当前待落实技术方向（不声称已迁移）。通用库保存知识/技能类型、理论、状态定义与规则；学科库保存具体实体、专业关系、错误类型、目标、任务、标准版本；按需公共专业库可复用语言学等知识；过程/组合定义可独立包或作为逻辑模块，避免强制一体系一库。实际个人记录、原始交互、授权、会话、计划由xLearn管理。跨库使用稳定ID、包ID与精确兼容版本，不使用外部自增ID；生成/发布时验证依赖与引用完整性。只加载任务需要的学科/核心/过程范围；显式绑定且优先类型级关联，例外需要依据。不将本地学习者库纳入知识包发布。
 
## 逻辑数据组（候选表名，不冻结schema）
| 对象组 | 候选表 | 关键语义 |
|---|---|---|
| 目标与能力 | goals, competency_dimensions, competency_requirements, goal_evidence_specs, standard_memberships | 构念与标准范围分离；成功证据与辅助条件 |
| 学习对象 | learning_objects, object_components, object_targets, learning_units, unit_memberships | 稳定实体引用、粒度、组成与先修分开 |
| 资源 | resource_descriptors, resource_bindings, modality_specs, content_quality_checks | 内容形式、质量、权利、可及性、适用范围 |
| 交互 | interaction_templates, interaction_roles, interaction_contracts | 输入/产出、提示、证据、能力需求 |
| 状态 | state_dimensions, observation_specs, estimation_model_refs, state_update_policies | 只存专业定义，不存个体事件或估计值 |
| 诊断补救 | error_patterns, diagnostic_hypotheses, diagnostic_evidence_specs, remediation_bindings, retest_specs | 多候选原因、条件、未知、复测 |
| 环境角色 | role_specs, environment_specs, capability_requirements, accessibility_constraints | 适用/权限要求，非实际授权 |
| 迁移 | transfer_tasks, transfer_conditions, assessment_specs, assessment_rubrics | 目标、任务、情境、时间、独立性 |
| 改进 | evaluation_protocols, evaluation_evidence, candidate_changes, review_records, release_manifests | 专业评价协议及合规汇总，候选与正式隔离 |
既有D011过程表通过稳定引用组合以上对象；避免重复表，DB01设计时对照同义实体与现有专业表。实际schema须给出约束/索引/引用验证、错误处理、备份与迁移及查询计划。
 
## 组合契约
目标+构念+学科范围→目标知识/技能/对象→资源与交互→过程模板与活动→观测契约→评分与状态估计→反馈/激励/补救→下一步或停止→保持/迁移评价。
输入必须保留精确版本、可用角色/工具、预算、环境和学习者选择；输出具有理由、依据、预计观测、可选替代和停止条件。实际执行与计分独立；知识库不运行任意脚本。允许动态切换及跨次恢复；升级不得改变历史会话证据。
 
## 状态与证据写入边界
Observation不可被推测或生成内容覆盖；Scoring/Estimate/SelfReport分别拥有身份、时间、方法、证据和不确定性；缺失不是零分、未掌握或动机不足。候选原因不写成个体事实。策略依赖的状态维度不能用不兼容代理量代替。学习者可拒绝激励、请求解释、暂停/退出；预算耗尽不得自动晋升。
 
## 外部改进门禁
E01执行评价必须绑定干预/对照、目标/指标、版本、适用群体/情境、证据资格和不确定性。实际实验原始个人记录留授权环境；公共库只使用合法可披露的协议、汇总、专业证据和候选修订。观测→候选改动→专业验证→独立审核→批准的版本清单；正式版本不接受直接写入、自动训练结果晋升或仅按参与时长优化。回退有独立版本记录和兼容检查。工程模拟、模型拟合和真实教育效果分别评价。
