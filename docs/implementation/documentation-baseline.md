# 当前建设事实与文档补齐账本（历史补齐及当前交接）
用户要求先补齐此前未文档化成果，再推进。以下整合已存在的文档、Issue证据和新保全归档，不生成新专业事实。历史补齐基于原待审HEAD；新R3-R #6 7211695681已ACCEPT_SCOPED，D014正式生效。以下历史状态保留，当前资格依正式收据。

| 项目 | 事实与证据入口 | 状态/后续 |
|---|---|---|
| 目标和历史决策 | [D001–D014](../product/decision-index.md) | D014明确文本优先；旧RDF仅保全 |
| 专业体系 | [K/H/P/A](../product/system/README.md)；[F/E](../product/system/learning-lifecycle-system.md) | 顶层候选，823分类/648 D3；非知识完成 |
| 数据库存及D4 | [结构库存](../drafts/s01-scope-inventory.json)、[来源校准](../drafts/s01-source-calibration.md) | 15已有D4候选，剩余逐D3拆分、逐源核验 |
| 知识格式 | [D014合同](../design/text-knowledge-package.md)、[导入映射](../drafts/db01-sqlite-design.md) | 候选，schema与工具未实现 |
| 动态过程 | [P体系](../product/system/learning-process-system.md)、[过程契约](../design/learning-process-contract.md) | 待专业填充及实际验证 |
| 生命周期与组合 | [生命周期契约](../design/learning-lifecycle-contract.md)、[CQ账本](coverage-ledger.json)、[LC矩阵](learning-lifecycle-acceptance.md) | CQ/LC NOT_RUN |
| HSK原始资料 | [来源登记](../research/hsk-source-intake.md) | RHSK01–03文本初读，其余多数仅元数据；原PDF身份/权利HOLD |
| HSK实际RDF导入 | [R2历史证据](hsk-import-r2.md) | 159708 quads，仅私有staging |
| 数据恢复与归档 | [SRC01](src01-readable-archive.md) / [JSON证据](src01-preservation-evidence.json) | 实际全量恢复及9类JSONL回读；整体PARTIAL |
| 调度 | [DAG](task-dag.md)、[执行合同](task-execution-contract.md) | 78节点420边，19波次；D014移除一边，P2新增两边，复算通过 |
| 发布 | G01/G03/G04/G05/REL01 | NOT_RUN/HOLD，无知识包发布 |

## 决策优先级与历史不变
D014优先于旧SQLite二进制产物设想；D013优先于D010专用RDF实现；D011/D012扩充原静态范围。历史执行记录不删除、不反向改称SQLite、不把候选抽取或归档等同学科知识。具体证据记录与当前状态分离。根README和文档入口改为当前状态；所有新增知识应优先可读源文件，条件、来源、反例与机器可导入记录同步写入，不把Issue评论或对话当唯一文档。

## 仍需补充的正式内容（不是当前完成项）
- G01：全域专业范围与来源校准、D3/D4需求账本、缺漏及边界，修复未核实源链接；已有书目线索不是全文资格。
- DB01/IF01：专业文本schema、稳定ID/关系/类型端点、源→命题→案例、语义与导入映射。
- SRC01：原PDF字节身份/视觉核对、许可范围及备份故障域；HS00/HSK01正式文本转换及字段对账。
- K/H/P/F/E/A：完整专业深度、实际结构化源文件、条件/反例、案例与引用，不能仅写分类。
- DB02/DB03/V00/V01/V02：实际文本校验、SQLite导入能力、闭环及CQ/LC验证；不直接生成持久SQLite文件。

本次选择集中整理而非新增独立审核。已取得R3-R裁定，本页不是任务完成收据。
