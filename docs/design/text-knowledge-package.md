# D014 — 人类可读知识源与 SQLite 导入合同（正式实施约束；专业schema待DB01/G04）
## 交付原则
用户明确先产出人类可读文件，能支持SQLite导入，不直接生成SQLite文件。权威事实源是分域、版本化、Git可diff的UTF-8文本；SQLite为只在下游明确需要时由导入工具构建的派生视图。禁止数据库内独有事实、反向把数据库作为编辑源、默认生成或发布.sqlite/.db、只写散文无法导入。

## 文件格式和目录
- Markdown：专业综述、理论解释、图示、复杂案例和使用指南。可供人读；若其中包含需要运行的知识，必须有结构化记录引用具体章节；不能让导入器靠LLM猜出事实。
- JSON（缩进、UTF-8）：对象、命题、条件、关系、流程、策略、案例、验证、包清单；统一schema、稳定ID。单一事实在一个权威记录中定义，Markdown解释可引用而不成为第二事实源。
- JSONL（每行一个完整JSON对象，UTF-8）：HSK词汇、汉字、标准成员、原始块等大规模同类型记录；稳定ID排序，按领域/版本/等级或批次拆文件，不强制单一巨型文件。CSV/TSV可作未来只含固定标量的受控交换或派生导出，不是当前必需；不采用未定义的双源格式。

```text
knowledge/
  core/K01/README.md
  core/K01/claims.json
  core/K01/relations.json
  chinese/H03/README.md
  chinese/H03/lexical-records/level-01.jsonl
  chinese/H07/standard-memberships.jsonl
  process/P06/README.md
  process/P06/feedback-flows.json
  composition/A03/cases.json
  manifests/
schemas/
importers/sqlite/
validation/
```
上述是目录候选，不强制全部目录同时建立。受限HSK原文及原始抽取保存在私有工作区，公开仓库只发布有权利资格的记录、原创设计和安全摘要；用户数据不进入知识包。

## 结构化合同
包清单包含package_id/version/schema_version、文件路径及SHA256、依赖包及精确版本/manifest digest、权利/资格/适用范围。每条记录含stable_id、kind、owner、status、版本上下文、专业字段、关系与条件、来源定位/证据/案例/验证引用及不确定性（按类型schema规定，不能用任意字段默默忽略）。关系端点是typed reference（package_id, stable_id, kind, version）；本地ID和跨包ID区分；跨包依赖按清单解析，禁止外部自增整数ID与隐式全库加载。来源、定位、命题、实体、关系、案例、验证分别定义。学习过程保存步骤、转移条件、事件、预算、终止、未知/失败/暂停分支与角色权限；不得储存任意可执行脚本。

## 转换与验证
1. 编写/抽取可读文本；保留原始字段、页码、序号和标准版本。规范化字段与原字段分开，未知显式标注。
2. 校验JSON/JSONL语法（拒绝重复key）、schema、稳定ID、类型、引用、版本、专业语义、状态、权利；不合格项不默默删除。
3. 形成分域可读包、版本manifest和对账报告；按需提供SQLite DDL、确定性映射和导入工具，用户选择目标时才构建数据库。导入器不得要求人工补写SQL事实、让LLM重新解析自然语言或把错误静默转为NULL。
4. 后续验证先在内存SQLite执行实际导入、外键、索引查询、数据/关系对账、重复输入及错误拒绝；文本包文件系统激活/回退另测。当前禁止直接生成SQLite文件；涉及持久SQLite文件的测试或正式部署只在用户以后明确要求时执行，未执行项记录HOLD。
5. 文本包的实际字节、schema、导入工具、测试预期、环境、专业资格、输入输出证据绑定版本；正式发布的是文本包、schema、映射、导入器和报告。数据库文件不是Git发布物或权威内容。

## 最小原创结构示例
见 [records.json](../drafts/text-package-example/records.json)，仅合成格式示例，不是已资格化知识。包含一条学科对象和一条类型绑定、一个带成功/失败/未知分支的过程模板。具体全视图schema、专业字段及实际导入验证由DB01/IF01/DB02完成。原HSK staging及备份保留，不因D014删除或直接生成数据库。
