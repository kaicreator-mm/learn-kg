# SRC01 — HSK 私有资料保全与可读归档证据（D014）
日期 2026-11-26。归属#5、总控#6。此处仅记录已经执行的历史和当前非破坏保全，非HSK01正式知识转换或独立验收。
 
## 既有备份与恢复
原R2抽取文本991684字节、导入代码、K/H分类文件及报告已复制到授权服务器私有持久目录（0700）；原/tmp源保留。Gateway job job_01M8BQJWJQ00YSZSNVCSNRAE3R 成功，完整N-Quads导出22815908字节，新隔离Store恢复后重开，逐quad集合一致：HSK图155619，分类图4089，共159708；无正式accepted图。抽取文本SHA256 34ca9f2d34a31809f86311d33e85f09350cb452d2c66a91f24f7548284dfba7f；NQ SHA256 4c4b309551934b49848bf6d518bab2b19db7a8d4ee262ac971b483b735184443；私有备份manifest SHA256 b0bdfa9db14aa1be65402a5bb60760d847002540007f6b44d0af317946a78555。历史执行 [#5 证据](https://github.com/kaicreator-mm/learn-kg/issues/5#issuecomment-7189899805)。
 
## 实际可读归档
Gateway job job_01M8BS5VDE004YJ6RYCC2HFYKY（成功）。从上述恢复Store只读读取，按graph+subject聚合，每实体必须恰有一个已知type，按类型分别输出UTF-8 JSONL。原始IRI、关系、数据类型、语言、字面量及图归属均保留；不增补词义、读音、构式、能力或教学关系。每行是完整对象，允许人工查看及机器解析。格式rdf-subject-jsonl-v1只用于归档，不是已冻结D014专业schema。
 
| 文件 | 记录数 | 字节数 |
|---|---:|---:|
| AbilityRecord.jsonl | 9 | 7472 |
| CharacterMembership.jsonl | 4288 | 4966898 |
| HanCharacter.jsonl | 3088 | 985072 |
| LevelBand.jsonl | 11 | 4463 |
| LexicalRecord.jsonl | 11000 | 14956767 |
| SourceBlock.jsonl | 94 | 254252 |
| SourceRecord.jsonl | 3 | 1644 |
| SyllabusVersion.jsonl | 1 | 494 |
| TaxonomyTopic.jsonl | 823 | 587325 |
| 合计 | 19317 | 21764387 |
 
使用JSONL实际读回每行，以IRI/字面量datatype/language重建Quad，拒绝重复graph+subject及不支持的RDF term。159708/159708四元组全量集合完全相等；排序quad集合SHA256 70c92f9fdea4cd5be7a22783164c7d1b82b04d6b2f7c7be02fc0c051f05a2d50 与先前恢复记录一致。归档manifest SHA256 7652d0b48b65179d56bcee96ebdcaa1f578d040e0fbcddbeff8da1ced26c70a2；各文件hash见 [机器可读证据](src01-preservation-evidence.json)。目录0700，未公开任何私有源字节或归档位置；未生成SQLite文件。实际执行脚本完整留在上述Gateway job；仓库仅保存格式、算法及校验摘要，不声称已实现正式通用导入器。
 
## 归档记录格式（纯合成示意）
每行字段 graph、stable_id、kind、type_iri、properties；properties键为完整predicate IRI，值为数组，每项为{"kind":"iri","value":"urn:example:object"} 或 {"kind":"literal","value":"示例","datatype":"http://www.w3.org/2001/XMLSchema#string","language":null}。RDF type由type_iri还原，其余属性逐项还原。数组保留多值，未知term拒绝。按graph+subject唯一，不能直接把裸subject当跨图唯一键。正式HSK01会在IF01/HS00之后另行转换为专业可读字段并逐字段对账，归档不替代专业结构。
 
## 当前未完成
RHSK01/02/03元数据回读：PDF分别4636209/3696686/73684字节，not_shared；连接器未返回原始字节hash，原PDF身份/视觉校对与权利仍HOLD。相同服务器持久副本不是独立故障域备份。旧RDF scopeTopic只代表范围位置，语义仍待确认。历史候选抽取不是合格学科事实。SRC01整体PARTIAL，无PRESERVATION_VERIFIED调度收据，不解锁HS00/HSK01。R3未裁决前不正式迁移。