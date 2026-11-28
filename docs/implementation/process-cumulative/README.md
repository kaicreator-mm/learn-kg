# P01–P10 统一流程候选快照（R2）

版本 0.1.0-process-candidate-2，受限候选，不是完整流程引擎、教育实证或独立资格。旧 P01/P02/P03 分包版本及原始收据原样保存；现有 DB01/IF01 不允许 learning-process 依赖另一 learning-process 版本，故采用单快照并仅迁移 490 条旧记录中的内部流程引用版本。migration.json 逐条保留原/新内容哈希；旧来源、事实、条件、案例预期不改。历史收据被替代但不删除，未登记任何独立资格。新版本所有跨 P 引用均为同包精确引用。

- P04：顺序及替代路径、两成员逻辑 ALL 汇合、声明的子流程返回、独立评价、一次补救重试、有限渐撤、预算和控制事件、同一次回放的暂停恢复与去重。不是实际并发执行、任意子流程调用或持久化恢复。
- P05：首学/生成式提取/时窗候选/独立延迟复测/陌生任务分离；具体分钟例计算学习间隔、保持间隔及下一候选时点，明确组块/混合、提示、策略选择字段。不声称最佳间隔或拟合个人模型。
- P06：评分版本与观测有效性、缺答/无效/未施测、辅助与独立表现、竞争解释及针对性建议、独立变式复测。具体合成二元评分例不代替一般量规/实际原因诊断。
- P07：只提供可拒绝的激励选项，退出/拒绝/暂停优先；匹配目标、评分版本、支持和单位的合成整数观测才描述变化。不诊断动机，不声称真实学习效果。
- P08：估计与不确定性、有限目标/预算/可及性/构念/权限筛选、本人选择及结果记录；具体候选集不自动执行，无可行或未知时澄清/延期。
- P09：即时、延迟、陌生任务迁移三条观察必须携带相同typed LEARNER_SUBJECT identity对象（稳定subject_id及identity_version）；三个event time固定为UTC epoch seconds/SECOND。recorded_at独立记录，只在recording clock stream内检查顺序，不与observed_at跨时钟比较。延迟由时间戳相减计算，至少86,400秒，novel严格晚于delayed；86,400秒仅是本候选协议边界，不是普遍或最优间隔。身份相等仅为协议绑定，不是真实身份认证；时钟来源准确度未验证；不声称真实延迟保持、迁移或掌握效果。
- P09 policy-to-flow gate：现有DB01 PolicySpec/CompositionSpec与IF01 typed refs无法表达绑定精确FlowSpec身份/版本、flow instance、input digest和COMPLETE结果的不可伪造依赖。因此移除P09 PolicySpec的SUGGEST规则；只保留ADVICE_ONLY REQUEST_OBSERVATION。专用wrapper从SQL重新加载同版本的精确P09.FLOW，并对同一input对象内部求值；不接受caller flow_result/flow_ref/flow_instance_id/input_digest。HOLD/STOP/PAUSE/FAILED/缺失/未知/错配均不进入REQUEST_OBSERVATION路径。未来若要恢复SUGGEST，必须先扩展受支持的canonical composition contract并重新独立审核。
- P09当前共93项有限案例，其中38项身份/时间正反例、12项policy-to-flow gate案例；8项原身份/时间边界测试和16项新policy gate测试通过，38/38独立参考计算对照通过。知识导入器37/37，IF01有限接口验证通过；所有结果均为受限合成协议验证，不是学习效果资格。
- P10：跨日计划与用户选择、精确版本及检查点、稳定事件 ID、冲突拒绝、预算、显式退出。具体检查点合成回放不构成真实持久性/事务性、认证或后台授权。

本次 P09 整改只改变 P09.jsonl canonical shard；P01–P08、P10 canonical JSONL 与原始 design.json 均按 BASE_HEAD 字节级保留。P09 新记录 provenance 指向独立 p09-remediation.json，避免因共享设计文件修改而重写其他模块。

design.json、p09-remediation.json、coverage.json 逐原始需求保留受限范围和未完成事项；canonical JSONL/manifest 是可读交付，实际内存 SQLite 导入，不生成持久数据库。build.py 从当前知识候选与资格绑定生成；semantic_checks.py 提供具体合成数值/条件案例；inherited.py 在新 SQL 快照回放旧作者用例。Case 中结构化期望用 canonical JSON 字符串存储，Validation 的结果摘要计算对应 JSON 值。当前 SQL builder replay 共360项；143项旧 P01–P03 用例是迁移回归，不是新增独立 oracle。新增加的12项P09 policy gate案例单独标记为P09_POLICY_GATE，不与P09 FlowSpec案例混淆。所有结果仅 BUILDER；通用执行器、现实干预效果、完整专业深度、源/权利清理、CQ/LC 与 G03/G04/G05 均未通过。

原 P01–P03 的额外专业限制和覆盖缺口继承，不因版本迁移而消失。P04–P10 中的布尔字段是明确提供的合成事实而非已实现的现实分类器；具体案例仍限各自专用方法。P04 支持逻辑汇合，不承诺通用并发、跨进程执行或实际调用下级 FlowSpec。P09 的 PolicySpec 不再有 SUGGEST 路由；只有内部精确 FlowSpec 同输入求值 COMPLETE 后才允许 REQUEST_OBSERVATION（ADVICE_ONLY），不推断保持、迁移、掌握或因果效果。P10 检查点摘要来自可信调用者的明确 pin，摘要本身不是身份认证。

当前状态：PREPARATION_ONLY；P09-only independent delta review PENDING；不写资格收据、不更新 Task DAG 注册、不创建 PR、不合并。
