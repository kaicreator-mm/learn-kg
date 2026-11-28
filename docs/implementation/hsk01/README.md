# HSK01 — 私有 HSK 可读文本转换与对账候选

状态：PRIVATE_CANDIDATE_CONVERSION_ONLY，未登记 HSK01 正式候选收据，待独立审核。HS00 已由 #31 审核通过并登记。消费 SRC01 限定保全、HS00 精确收据、IF01 接口；权利、历史 PDF 字节身份、视觉版式和权威标准身份继续 HOLD。

## 权威文本及派生视图

源档案保留不修改。对九类记录逐条生成 UTF-8 JSONL：原始 RDF graph/subject/type/predicate/term 完整存于 raw_rdf；provenance 包含原文件、行号、精确原始行摘要；candidate 是派生索引，显式类型、候选稳定 ID、原字段指针/摘要、来源定位、类型链接、语法级别解析和 DB01 映射边界。归档记录的全部原始值和未知字段均可检索，不以规范化值覆盖。原始 JSONL 可按原格式逐字节重构。候选 ID 不代表已认定的 Lexeme、能力、正式汉字或其它语义身份；normalized_knowledge_id 为空，未生成专业命题或教学关系。

## 转换范围

| 原始类型 | 记录数 | 候选用途 |
|---|---:|---|
| LexicalRecord | 11000 | 原词形与 readingPosRaw 分开索引，等级原值及句法候选；H03 解析义项/读音/词性 |
| CharacterMembership | 4288 | 认读3088、书写1200，独立来源成员关系 |
| HanCharacter | 3088 | 字符身份与 Unicode codepoint；不推断读音/部件 |
| SourceBlock | 94 | 53任务、20话题、21语法；原文本和来源摘要；H04/H05 分析 |
| AbilityRecord | 9 | 来源能力原文本；H06/H07 专业映射 |
| TaxonomyTopic | 823 | 原分类父子引用；不是先修或掌握关系 |
| LevelBand | 11 | HS00 pinned archive 等级证据 |
| SourceRecord | 3 | 来源身份及保全证据 |
| SyllabusVersion | 1 | 来源声明版本，权威身份 UNKNOWN_HOLD |

28种词汇等级原标签、102条括号等级记录保持原值；不因标点、单字词或同形而去重。PDF index 与 page number 均为空，printedPage 原值独立保留，数值仅语法候选。scopeTopic 只代表来源范围定位。缺字段、错类型、目标不存在、同名谓词冲突或身份歧义拒绝；未知附加字段原样保留。

## 文本与导入

build_hsk01.py 消费外部可信的 HS00 收据 SHA256，核验收据工件、HS00 pin、归档 manifest、九个文件及每条原始行。新输出目录必须在 Git 工作区外，0700，文件权限由 umask 077 限制。转换并读回后逐文件重建原归档字节，使用内存 SQLite 对 graph/id/kind 三元端点建 registry/edges，实际 FK 校验；不创建 SQLite 文件。mapping-contract.json 定义九类到 DB01 的逐字段映射及未满足的专业证据字段；此阶段不是 DB01 canonical package 注册，也没有调用拒绝私有数据的通用 importer，DB03 仍须完成私有适配与全视图校验。stage.schema.json 是私有 staging 形状，语义绑定由生成器与后续独立审核检查。

运行：python3 docs/implementation/hsk01/build_hsk01.py --archive "$SRC01_ARCHIVE_ROOT" --output "$HSK01_NEW_PRIVATE_OUTPUT" --hs00-receipt-sha256 "$TRUSTED_HS00_RECEIPT_SHA256"

测试：python3 docs/implementation/hsk01/test_hsk01.py

conversion-evidence.json 仅含数量、摘要、权限和回放证据；原始及派生语料不进入 Git，原始路径/Drive ID 不写入仓库。独立复核可在授权服务器私有目录重建新输出并校验安全摘要。无需将私有语料下载到其他对话。当前数据不能公开、不得据此声称 H01–H07 已完成、专业资格、真实学习效果、CQ/LC、DB03、G03/G04/G05 或发布已通过。
