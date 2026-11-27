# R2 实施与证据合同（待有限独立复审）
## RV01 / RV08：候选与资格、调度
任务标识 TASK:<id>，历史case-pilot P01–P04保留别名 CASE-P01–04。#6不是master，#1主线/#2版本/#6调度。每个任务单独收据路径 evidence/tasks/<id>/<attempt-id>.json（私有内容仅写安全摘要与hash），含task_id、attempt_id、operator/session/role、branch/base/exact_head、contract_id/hash、input[]（task_id、receipt_id、content_digest、版本、具体引用）、output[]（path/sha256/类型）、验证与日志定位、状态、问题及时间。独立资格收据另含reviewer、被审内容digest、消费tuple、P0/P1/P2及裁决；reviewer不得是对应写作者。内容digest覆盖规范化输入与artifact清单，不把后续review comment自身纳入digest。记录到对应issue并用CAS推进；冲突重新读取，禁止覆盖旧收据。
 
状态：PLANNED→READY→RUNNING→CANDIDATE_READY / BLOCKED / FAILED；SRC01单独PRESERVATION_VERIFIED；批次审核逐模块 QUALIFIED_LOCAL 或 REWORK_REQUIRED，批次输出QUALIFICATION_RECEIPTS；G01/G03/G04/G05单独GATE_ACCEPTED；REL01 RELEASED。READY仅静态前置结构满足，实际执行须检查当前调度政策与有效收据；缺少/冲突/未知一律不推进。R2审核未通过前仅SRC01非破坏保全、S01/DB01调查草案。
 
候选依赖可在独立资格前用于候选下游，禁止最终接受/发布。审核可以按原批次进行，逐模块审查本身与确切消费候选；局部资格不代表所有上游已资格化。G03检查每个模块当前digest及全部消费tuple与获准当前digest一致，且对应局部资格收据有效；F/A/E由G03独立裁决。若上游digest/接口/适用证据改变，遍历反向依赖并核对收据：将实际受影响下游的旧消费/资格/验证收据标记STALE，不能参与冻结；重新绑定、执行受影响验证、有限独立复审，保留原收据。不影响的范围须有可核验不变性证据；无法判定按受影响处理。不在DAG添加回边，不强制等待整批审核导致循环。G03/G04/G05已完成时同样撤销受影响裁决，禁止REL01基于STALE。例：K02 v1→K05/P05，KR01要求K02 v2，则原K05/P05及其实际下游收据不得用于G03；重新绑定v2及复验，独立复核变化范围；若仅审核元数据变化且content_digest未变，不自动作废内容，但仍核对资格状态。
 
## RV02 / RV06：早期接口
IF01 由S01/G01和DB01候选共同提供版本化最小公共对象：Goal/Competency、KnowledgeRef/SkillType、LearningObject、Resource/Modality、Activity/Interaction、Role/Environment、ObservationSpec/StateDimension、Policy/Condition、Source/Claim/Case/Validation。每个引用包含owner/package/stable_id/type/version/适用条件，跨域错误类型/版本/未知明确拒绝。F定义/接口先于P模板在IF01确认；F最终实例在P/H/K候选输出后验证。早期接口不是G04冻结；后续变更按上节失效。HS00先给标准版/源记录/等级身份，H02/H03/H04可独立研究语义候选；最终H05/H06/H07组合依赖及F/A实际消费仍必须完整。原D4专业主责不变。
 
## RV03：SQLite与规范创作格式
DB01需冻结候选交换字段（JSON或JSONL规范schema）：package_id/version, stable_id, owner, kind, typed endpoints, source_locator, claim_type, conditions, status, evidence_refs, case_refs, validation_refs。Source、Locator、Claim、Element、Relation、Case、Validation分对象；K/H/P/F/A/E均用同一身份/来源契约加专业字段，保存原记录及不确定性。DB02/DB03实现结构化输入→SQLite，逐类数量/字段/关系与拒绝原因对账，不允许依赖人工重写。各库独立原生FK、每连接PRAGMA foreign_keys=ON并检查foreign_key_check/integrity_check；跨库由显式resolver验证package/stable_id/type/version/status/权利，不假定原生跨库FK。读者只加载已批准manifest指定文件和相关域，按需路由；无关库不打开、不查询；类型关联优先，例外有证据，记录边数与EXPLAIN QUERY PLAN。
 
发布采用单写者、独立候选目录、不可变内容寻址包，生成完整依赖manifest（schema、输入、资格、文件hash、权利、验证及批准身份）。在独立临时路径校验全部文件、resolver及权限；完成持久化与目录/文件同步后，通过同文件系统单一manifest指针原子替换激活，读者固定一次manifest快照，不混合版本；保留旧包/指针以回退。具体平台原子性及同步保证由DB02实证，不声称ATTACH+WAL跨文件原子。失败或中断不得暴露部分新版本，测试激活前/后中断、错版本/类型/缺失包、篡改hash、重复导入、恢复旧指针、读取期间切换、候选/个人/私有数据泄露拒绝。正式激活仅REL01。SRC01先私有导出/恢复验证再迁移，保留原RDF与原始抽取；无权利资格数据不公开。参考SQLite官方 https://www.sqlite.org/foreignkeys.html 与 https://www.sqlite.org/lang_attach.html （设计依据，具体实证待DB02）。
 
## RV04：原型、冻结与实跑
V00有限候选原型，仅列实际case与输入/代码/env/输出digest；不等待全部专业模块。V01须A01–08及F/E/P/H、DB03和V00候选完整绑定，建立CQ/LC具体夹具和独立预期（预期独立于被测结果）；允许在G03前执行，不宣称最终资格。G03冻结专业内容manifest，G04冻结获准输入、schema/接口/工具、fixture/oracle及环境合同；V01受改变影响的收据须重验/重新绑定，不把候选结果当最终验收。V02按冻结tuple重新生成包，执行逐项正负例，记录实际字节hash、输入manifest、代码、环境、oracle、fixture、查询计划、性能与回退。G05独立核对实际字节、复跑有限关键测试及资格/覆盖闭包，REL01仅激活批准hash。工程测试、模型拟合、真实学习效果三种证据分开。
 
## RV05：可检查覆盖
coverage-ledger.json 当前是任务路由与必需字段模板，所有CQ/LC NOT_RUN。S01逐D3列D4需求或明确不适用/遗漏原因；每D4唯一owner、claim类型、来源状态、条件、反例和案例。G02每模块提交规范化记录与逐D3/D4证据账本，适用时正向/逆向/干预/反证、独立数值oracle；不得以平均配额或链接计数验收。G03校验所有D3覆盖、D4唯一且可追踪、每CQ owner/route/fixture/oracle存在、适用性及专业资格，G04冻结预期，V02记录实际结果/失败及理由，G05逐项裁决。非适用/真实教育实证缺失显式HOLD或NA且有范围裁决；不能计入PASS。每个LC独立预期与负例，不用文字关联替代实际运行。
 
## 修正账本
RV01 receipt语义+失效；RV02 IF01和缺失F/A边；RV03 DB01–03/V02/REL发布；RV04 V00/V01/G03/G04/V02/G05精确绑定；RV05 全CQ/LC账本与逐D3/D4；RV06 HS00与H并行；RV07 历史RDF入口标识和issue职责；RV08 master/调度/CASE命名/收据。全部为修正候选，待独立复审，不标CLOSED。

## D014 优先级覆盖（用户新增交付要求）
此前RV03/RV04中的“SQLite候选包/最终包/激活”在本版本实施交付上以文本知识包为准：权威输入与发布为可读UTF-8文本、schema、映射、导入器和验证证据。DB02/03支持显式下游导入；本项目不直接生成持久SQLite文件，不将SQLite文件作为正式知识产物。默认用内存SQLite执行正负导入与查询测试；文本manifest可在文件系统做实际中断/回退测试；涉及实际多文件SQLite崩溃或文件级事务的保证，未实测明确HOLD，不能由内存测试外推，未来经用户要求另行执行。G03/G04/G05/REL绑定获准文本实际字节及导入器版本，保持原资格/失效/权限约束。详见 [文本合同](../design/text-knowledge-package.md)。
