# DB01 文本知识包与 SQLite 导入映射 — 调查草案
规划基线 05a0a759bc10051adefd3eb966f16694cb2c03fc。R3尚未裁决；本草案不冻结schema、不迁移私有源、不作为DB01完成收据。
 
D014 优先：以下SQLite文件名仅为未来下游可选导入映射示意，不是本项目要生成的文件。先按 [文本知识包合同](../design/text-knowledge-package.md) 写可读源文件。

## 1. 逻辑包与未来导入映射
| 包 | 所有权与表组 | 默认加载 |
|---|---|---|
| learning-core.sqlite | K理论、机制、知识/技能类型、状态/测量/数学模型、策略/证据 | 涉及学习决策时 |
| chinese.sqlite | H汉字、读音、词汇、义项、语法、语用、任务、能力、HSK版本和成员 | 汉语任务 |
| learning-process.sqlite | P模板、步骤、转移、反馈、激励、评价、F/A/E组合定义与显式类型绑定 | 需要模式或调节时 |
| optional professional shared | 语言学等确有跨学科复用的专业实体 | 仅声明依赖时 |
| other-subject.sqlite | 各学科独立专业表；LC11首版仅最小样本 | 对应学科 |
| staging / authoring | 私有源、原始字段、候选、争议、来源权利及审查 | 仅建设者 |
| learner.sqlite | 实际学习事件、个体状态、会话、计划、授权，归xLearn | 仅授权运行任务 |
无强制一域一库。chinese只依赖所需通用类型；process通过类型和契约引用学科，具体组合声明所需学科；禁止反向循环物理依赖。通用包不直接引用每个学科实体。学科内部一条词汇记录不能直接生成多个无证义项或全部策略边。
 
## 2. 公共身份与专业表
每包有 package_meta、entity_registry(stable_id,kind,owner)、sources、locators、claims、claim_evidence、case_specs、validation_specs、relation_types、local_relations、external_refs。registry仅作身份/类型，不用JSON巨型属性表替代专业字段。实体ID用包命名空间稳定文本；本地整数可作内部索引但不可出库。每个本地外键连接开启foreign_keys，类型端点由约束/触发器或生成器校验；跨包ref含 package_id,version,stable_id,expected_kind,content_digest,relation,conditions，resolver验证存在、版本、类型、权利、资格和关系允许方向。跨文件没有原生FK，拒绝错误引用。来源/定位/命题/关系/案例/验证分离；状态、条件、适用人群、不确定性、竞争命题均保留。数值模型独立参数、适用域、公式版本、oracle；规则只使用声明式表达式或经批准函数ID。
 
汉语候选表：han_characters, character_readings, character_components, lexemes, lexical_readings, senses, lexeme_relations, constructions, construction_conditions, language_skills, performance_tasks, standards, standard_levels, source_lexical_records, source_character_memberships, source_blocks, source_ability_records, semantic_mappings。源记录稳定ID是标准版本+表/区段+原序号，不等同lexeme/sense；同形词、原始读音词性串、原等级串、括号级别及合并7–9保留。未分列表块留LAYOUT_REVIEW_PENDING。
 
过程候选表：modes, activity_templates, flow_templates, flow_steps, flow_transitions, conditions, role_specs, observation_specs, feedback_policies, motivation_policies, assessment_policies, adaptation_policies, type_bindings, composition_templates。流程允许有界循环；transition(source,target,event,guard,priority,unknown_branch,budget,checkpoint)；每个模板有入口、终止与不可执行语义，历史会话绑定版本。知识图谱不是运行时，实际观察/状态不写这些表。
 
## 3. 查询与索引
字/词直接专业表索引；词义/读音/构式经本地JOIN；父子/必要先修使用单独有类型关系与递归CTE，不能混合分类、等级和因果。关系索引(source,relation,target)及(target,relation,source)。标准成员按(version,band,mode,ordinal)，按稳定记录ID反查。过程按(knowledge_type,skill_type,goal_kind)选类型级策略，再匹配条件，不复制每词策略。仅开启请求路由的数据库连接并记录实际打开库；查询计划和扇出计数由DB02实测。HSK精确字词用B-tree，中文FTS/tokenizer另按实际需求试验，不承诺默认分词。
 
## 4. 下游可选数据库构建与文本包发布
结构化JSON/JSONL权威文本→schema/语义校验→逐类对账→不可变文本manifest。SQLite仅派生导入映射；后续默认内存验证，当前不生成持久数据库文件。以下物理库一致性要求仅供下游显式导入时实现，未经实际文件测试不得宣称保证。读者固定一次manifest快照，从已批准版本路径只读打开文件，不使用任意外部路径。单包单写者；临时目录、完整文件/目录同步，再同文件系统原子替换单一manifest指针；旧manifest及文件保留供回退。SQLite ATTACH 跨文件原子性不适用于主库内存或WAL情形，不能依赖它保证跨包发布。验证平台语义、崩溃窗口、读者持有旧版本、切换后新读者、篡改hash、缺依赖/错版本、恢复失败。REL01仅发布文本知识包，不激活SQLite数据库。
 
官方参考： https://www.sqlite.org/foreignkeys.html 及 https://www.sqlite.org/lang_attach.html （本轮网页核验）。仅设计依据，不是实际事务或性能测试。
 
## 5. HSK迁移映射与对账
| RDF输入 | SQLite候选 | 必须核对 |
|---|---|---|
| TaxonomyTopic | 分类表 | 823，父路径与scope语义 |
| LexicalRecord | source_lexical_records | 11000，逐字段，102括号级别原样 |
| HanCharacter | han_characters | 3088，字符身份 |
| CharacterMembership | source_character_memberships | 4288，认读/书写及合并级 |
| SourceBlock | source_blocks | 94，类型/页/原文，保持未分列 |
| AbilityRecord | source_ability_records | 9，等级描述 |
| SourceRecord/SyllabusVersion/LevelBand | sources/standards/standard_levels | 原页码/序号/版本/权限状态 |
源与现有RDF保全后方可迁移。四元组数不要求与行数相等；比较原字段、语义、来源和差异账本。仅私有staging；权利未知不公开。ScopeTopic需逐型验证，不由范围推出先修。
 
## 6. 仍需DB01/IF01确定
最终专业列/主键与关系端点矩阵、canonical schema、跨包依赖最小化、身份版本规则、证据资格与状态机、生成失败语义、可复现实验数据和预期。DRAFT only；无SQL实施、性能基准、迁移或发布。