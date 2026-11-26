# DB01 — 图数据库设计 R1（可执行基线，未冻结）
D010 / #4。首版采用 RDF 1.1 数据模型、SPARQL 1.1 查询、PyOxigraph 0.5.13 嵌入式持久化（RocksDB）。选型理由：跨学科稳定IRI、显式语义、来源/命题分离、命名图隔离及 N-Quads/TriG 可移植。Neo4j 属性图便于关系遍历但非当前标准知识交换主模型；将来允许无损投影，不双写两套事实源。参考 https://pyoxigraph.readthedocs.io/en/stable/ 与 https://www.w3.org/TR/rdf11-primer/ ；未进行性能横向基准。
 
## 逻辑分层
| 图 | 用途 | 当前 |
|---|---|---|
| graph:staging:taxonomy:r1 | K/H 分类节点及 parent 结构，非专业事实 | 实际导入 |
| graph:staging:hsk:2025-11 | HSK原始抽取记录、来源、版本、范围、源块 | 实际导入 |
| graph:accepted:<release> | 独立审核及版本门禁通过的专业知识 | 未创建；默认消费只查已发布版本 |
| graph:cases:<release> | 案例、输入、预期、证据、验证 | 计划 |
| graph:decisions:<release> | 规则、条件、策略、风险；非个体实时状态 | 计划 |
| graph:manifest:<release> | 图版本、源散列、验证与发布清单 | 计划 |
命名图是查询与版本隔离，不是安全 ACL；staging与accepted发布物在物理/权限层进一步隔离，未实现外部查询服务。个人学习数据不进入公共知识库；xLearn独立保存学习事件和状态。
 
## ID 与节点
前缀 urn:learn-kg:，谓词 urn:learn-kg:schema:。TaxonomyTopic 用 taxonomy:<K/H路径>；分类边 parent 不是 prerequisiteFor。HanCharacter 用 han:<Unicode码点十六进制>；不从字形推导读音、部件或词义。
HSK规范记录使用稳定版本+源序号，LexicalRecord 不等于独立词义/词汇实体，原序号含多义/编号和同形词必须保留；后续显式 Lexeme、Sense、Reading、PartOfSpeech、Construction、Skill、Task、Topic、LevelRequirement 等专业类型，语义实体 ID 不直接复用源表序号。
- SourceRecord、SyllabusVersion、LevelBand：RHSK文件记录、规范版、合并等级范围分别表示。文本哈希不是 PDF 文件哈希。
- LexicalRecord：ordinal、levelRaw、headwordRaw、readingPosRaw、source、printedPage、levelBand、scopeTopic、status。levelBand仅表示原等级串的首段（非完整等级语义）；括号串不展开，7-9不拆分。
- CharacterMembership：ordinal、mode、levelBand、character、source、printedPage、scopeTopic、status；区分认读/书写及1-2合并书写。
- SourceBlock：blockKind、rawText、printedPage、levelBand、source、scopeTopic、status；语法/话题/任务尚未分列为原子节点。
- AbilityRecord：levelBand、rawText、source、scopeTopic、status。
- scopeTopic 只表示来源记录在知识体系的覆盖位置，不表示学科先修或因果。跨图关联需存在合法 taxonomy 目标。
 
## 未来专业命题结构（设计，不是实现）
Source→EvidenceLocator→Claim→subject/predicate/object；Claim 节点保留类型、适用条件、群体、版本、证据方向、争议、状态、审核凭证、效应及不确定性（适用时）。直接语义边只能由明确规则从合格Claim物化；保留回溯路径。Claim 的竞争关系与依赖显式建模；不能自动把相关、分类、共现、考试等级变为必要先修或因果。Cases 按正向、逆向、干预、反证四视角连接具体Claim/D4；学习者个体状态仅由下游维护。
 
## 导入与版本门禁
输入为指定RHSK01–03的连接器抽取文本JSON（私有）和固定R1两个分类文件。全量页序/词汇序号/字表序号、来源定位、完整与节选字段差异统计；无法可靠分列的源块只做LAYOUT_REVIEW_PENDING。先构建新目录并查询检查，再同一文件系统改名为候选目录，拒绝已有目标；不是生产发布事务/并发锁。本轮实现精确锚点查询、跨图关联、重开数据库、accepted 空、禁止臆造先修、错误序号和重复目标拒绝。后续补并发锁、全字段约束、SHACL或等效验证、N-Quads导出/回读比对、备份恢复、访问控制、源字节与许可资格、专业审核及发布清单；候选目录不得被当作发布版。
 
## 查询例
```sparql
PREFIX kg: <urn:learn-kg:schema:>
SELECT ?word ?page ?raw WHERE {
  GRAPH <urn:learn-kg:graph:staging:hsk:2025-11> {
    ?r a kg:LexicalRecord ; kg:levelBand <urn:learn-kg:band:1> ;
       kg:headwordRaw ?word ; kg:printedPage ?page ; kg:readingPosRaw ?raw .
  }
} ORDER BY ?word
```
显式staging供建设核验。生产接口必须限定批准的release图，不能默认查询全库或staging。下游通过稳定IRI与版本化查询/导出消费，不直接依赖RocksDB文件内部格式。
