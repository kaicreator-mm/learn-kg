# HS00 — HSK 标准与来源记录接口（候选）

**状态：CANDIDATE_PREPARATION_ONLY。** 本目录定义 HSK01 后续可消费的来源/标准接口，不代表 HSK 专业内容已审核、标准身份已确认、版权已清理或语料已转换。对应实施任务为 Issue #22；独立增量审核必须在后续任务中完成。

## 本阶段交付

- schema.json：JSON Schema 2020-12，定义来源记录、标准身份、等级标签、来源定位、原始字段捕获和显式记录类型。
- interface-contract.json：HSK01 消费合同、DB01/IF01 边界、版本/来源身份、摘要和 HOLD 规则。
- source-mapping.json：基于 SRC01 保全档案生成的机器可读映射。仅保存来源元数据、稳定 ID、页码/主题定位和摘要，不复制 PDF 或原始提取文本。
- db01-projections.json：109 条 DB01 Source / Standard / StandardBand / Locator 形状投影，以及 1 条单独标记的合成 SourceMembership 示例；所有投影均为 HOLD。IF01 typed-ref 仅验证结构，不注册 package。
- fixtures.json：11 个正向和 13 个负向有限示例。
- build_hs00.py：从私有 SRC01 档案、PDF 副本及保全证据生成来源映射。
- build_hs00_contract.py：确定性生成 Schema、DB01 投影、fixtures 和 interface contract。
- test_hs00.py / verify_hs00.py：有限接口、边界和保全验证。

## 来源与身份

SRC01 保全档案中存在 3 个来源记录：RHSK01、RHSK02、RHSK03。每个原始 PDF 当前版本的字节 SHA256 均在 Google Drive、Aliyun 和 V100 副本之间一致；隔离恢复验证为 3/3。RDF/可读档案 17/17 文件在独立恢复副本中逐字节一致。历史 SourceBlock 重放 94/94 精确，连接器文本当前/历史匹配 3/3。

- 当前 PDF 字节 SHA256、规范连接器文本 SHA256、SourceBlock JSONL SHA256 分开保存，不互相替代。
- 每个 PDF 只有一个当前 Drive revision；没有可用的上一 revision。安全证据未记录 Drive file ID、原始目录路径或精确 revision ID，因此这些字段显式为 NOT_STORED / NOT_CAPTURED，不推测。原始文件名保留自私有备份清单。
- 历史 PDF 原始字节 SHA256 缺失，保持 HOLD_NO_HISTORICAL_RAW_DIGEST。
- SourceRecord ID（例如 urn:learn-kg:source:RHSK01）与后续 Lexeme/HanCharacter/Topic 等规范知识 ID 是不同身份空间，禁止复用。
- 来源权限 HOLD_NO_PUBLICATION_OR_REDISTRIBUTION，可见性 PRIVATE_ONLY；不复制原始 PDF、完整提取文本、Drive ID、私有路径或下载链接。

## SourceBlock 与页码

当前保全包包含 94 个 SourceBlock，全部关联 RHSK01：

| 类型 | 数量 |
|---|---:|
| Task | 53 |
| Topic | 20 |
| Grammar | 21 |

SourceBlock 映射保留稳定 block ID、SourceRecord ID、LevelBand IRI、scope topic IRI、block 状态、逐字段摘要和 rawText UTF-8 长度/SHA256。主题引用分布为 H07.03.01（53）、H07.03.02（20）、H07.03.05（21）。

SourceBlock 当前记录的 printedPage 是 RDF xsd:integer 值，记录范围为 2–54、56–75、383–403。这些只是档案记录的页标签值，不是对 PDF 页面图像的视觉复核。当前 SourceBlock 没有可靠的逐块 PDF 零基页索引或一基页号，二者保持 UNKNOWN/HOLD；禁止从 printed page label 推导。

## 标准版本与等级标签

源图中的 release label 原样保留为 2025-11，图中状态为 STAGING。内部候选版本 hsk-2025-11 只用于候选引用；权威标准身份保持 UNKNOWN_HOLD，H07 最终标准映射未执行。

档案中有 11 条 LevelBand 记录；LexicalRecord 中观察到 28 种不同原始 level label，其中 102 条带全角括号的记录。解析器 hs00-level-label-parser@0.1.0 只做严格语法解析：
- 保留原始标签及全部括号、范围和标点；
- 把已识别的单数字/升序范围解析成候选成员等级；
- 用源标准 ID 与原始标签精确值生成 punctuation-sensitive merged-level identity；
- 不把解析结果视为官方等级语义或成员资格；
- 缺失、未知、格式错误、重复或有歧义的值保留 raw value，并返回 HOLD_UNPARSED，不修剪、不改写、不猜测。

## HSK01 消费约束

1. 来源 ID、当前 PDF 摘要、连接器文本摘要、SourceBlock 摘要和保全范围作为不可变来源证据传递。
2. 不从文件名、来源别名、图命名空间或版本字符串推断权威标准身份；UNKNOWN/HOLD 必须向下游传播。
3. 任何 level label 的规范化前必须保留精确 raw string；候选成员等级不能自动变成标准成员资格。
4. source_record_id 与 normalized_knowledge_id 分离。
5. record_kind 必须显式声明：VOCABULARY_ITEM、CHARACTER_ITEM、SOURCE_BLOCK、CAPABILITY、CATEGORY、CHARACTER_MEMBERSHIP。禁止根据字符串长度、Unicode 形状或字形数量推断词汇/汉字类型。
6. 定位必须分别表示零基 PDF 页索引、一基 PDF 页号和 printed page label；只在直接证据存在时填写前两者。
7. 原始字段、规范字段、解析器名称/版本、解析状态、来源定位和 raw-field SHA256 分开保存。未知字段可查询且不得静默丢弃。
8. 历史 PDF 身份、版权、视觉版式和发布权限 HOLD 必须传递到每个派生记录及输出。

## DB01 / IF01 边界

DB01 与 IF01 现有 schema/contract 未修改。所有 109 条 DB01 投影及 1 条合成 SourceMembership 形状示例通过当前 DB01 canonical schema；5 个 typed-ref 示例通过 DB01 ref schema。候选 package ID/version 只是结构示例，未创建 package manifest，也未注册到 IF01。合成 SourceMembership 不属于 HSK01 转换结果。

当前验证结果：HS00 Schema 通过；28/28 有限测试通过；5 个生成产物连续重放的 SHA256 全部一致；git diff --check 通过。以上是候选接口验证，不是独立资格。

## 运行与验证

生成器从本机私有档案运行；以下环境变量应由执行环境设置，不要把私有路径或 Drive ID 写进仓库：

    python3 docs/implementation/hs00/build_hs00.py --archive-root "$SRC01_ARCHIVE_ROOT" --restore-root "$SRC01_RESTORE_ROOT" --private-backup-manifest "$SRC01_PRIVATE_BACKUP_MANIFEST" --pdf-root "$SRC01_PRIVATE_PDF_ROOT"
    python3 docs/implementation/hs00/build_hs00_contract.py
    python3 docs/implementation/hs00/verify_hs00.py

## 明确未完成

HSK01 全量词汇/汉字/能力/分类转换、来源专业内容复核、H07 最终标准映射、CQ/LC、语义资格、历史 PDF 身份证明、版权确认、视觉版式审核、公开发布、SQLite 文件生成、Task DAG 完成登记、资格收据、PR 和合并均不属于本阶段。不得把当前候选接口描述为已完成 HSK 知识库。

### #24 增量整改

HSK01 消费须调用 hs00_semantic.HS00Validator.from_pinned_files(directory, expected_contract_sha256)，其中摘要来自外部受信的精确审核元组，而非待验证输入；validate(record, expected_kind) 成功才允许候选消费。Schema 仅形状校验。来源定位绑定精确 source/block/hash；实际 RDF locator 不允许从 printed label 推断 PDF 页。合成 locator 不构成真实来源。所有未解析/空白原始标签完整保留，成员与 merged identity 为空，未解析 band 不投影 DB01；RDF 原始 term 摘要与 raw UTF-8 字符串摘要区别保存。所有六个独立 record-kind 示例显式附带限制。原始 24 fixtures 不删，新增全对象变异、未知值及 pin 验证。
