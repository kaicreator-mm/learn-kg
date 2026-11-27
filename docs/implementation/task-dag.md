# v0.1.0 正式 Task DAG — D013 R3-R / D014
R3-R #6 comment 7211695681 / #2 7211696630，审查HEAD 05a0a759bc10051adefd3eb966f16694cb2c03fc，ACCEPT_SCOPED；8/8原问题关闭。唯一P2修正G03显式V01/DB03前置。D014文本优先，不生成持久SQLite。候选、资格、冻结、发布独立；详见[实施合同](task-execution-contract.md)。

## 任务账本（78节点，420边，19波次）
| ID | Issue | 前置 | 任务 | 交付 | 验收 |
|---|---|---|---|---|---|
| S01 | #3 | — | 专业范围与来源校准 | K/H/P/A/F/E范围库存、D2/D3/D4需求与主责、CQ01–26逐项路由、LC覆盖、来源及资格计划、HSK标准候选 | 按 coverage-ledger.json 模板生成机器可读清单，逐D3覆盖/遗漏理由、唯一主责、适用性、条件/反例/证据；核对D001–D015，不伪造事实 |
| G01 | #3 | S01 | 范围累计独立审核 | 范围及CQ/D4需求账本独立裁决 | 独立exact SHA；逐域、CQ、遗漏/不适用理由、来源发现状态完整；P0/P1关闭，P2明确处置；非专业命题资格 |
| DB01 | #4 | — | 人类可读知识源格式与SQLite导入映射设计 | 分域文本包、JSON/JSONL schema、Markdown专业说明、稳定ID及类型端点、版本依赖、SQLite表映射和文本包发布设计 | 文本是唯一事实源；字段和关系可直接解析，无手工二次编写；跨库类型/版本/权限resolver，候选/正式/个人隔离；无SQLite文件生成；G04冻结 |
| DB02 | #4 | DB01 | 文本校验器与SQLite导入工具 | 规范解析、语义校验、导入API/CLI、SQLite DDL与映射、拒绝原因、可复现测试 | 文本先校验；内存SQLite实际FK、类型/孤儿/版本/缺包拒绝、重复导入、路由/EXPLAIN；默认不写数据库文件。持久输出仅下游显式选择，当前不执行；物理跨库崩溃测试未授权则HOLD，不伪报；文本manifest激活/恢复测试 |
| SRC01 | #5 | — | 保全既有HSK来源和RDF staging | 非破坏性原始来源与RDF/抽取文本保全；备份manifest、hash、导出和独立恢复记录 | 实读既有数据、导出并在隔离位置恢复比对；原PDF身份/权利、文本hash与PDF hash区分；缺失明确BLOCKED/HOLD；禁止公开全文及删除原数据 |
| HSK01 | #5 | SRC01, HS00, IF01 | HSK人类可读源文件转换与对账 | 私有UTF-8 JSONL/JSON原始记录及语义候选文本、RDF/源逐字段映射、差异账本与导入映射 | 11000词汇/4288成员/3088字/94源块/9能力/823分类逐类对账；102括号级别、合并级、页序号/原始字段、来源身份和scopeTopic语义；可阅读且可解析、未知保留、权利不明保持私有；不生成SQLite文件 |
| K01 | #6 | G01, IF01 | 学习理论与科学基础模块专业深化 | 全域D2–D4、逐原子知识及来源定位、条件/反例、关系/组合案例、CQ及验证；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 模块完整覆盖账本，主责明确；事实/模型/策略分离；有条件适用和负例，不按知识点数量验收；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| K02 | #6 | G01, IF01 | 认知、记忆与注意模块专业深化 | 全域D2–D4、逐原子知识及来源定位、条件/反例、关系/组合案例、CQ及验证；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 模块完整覆盖账本，主责明确；事实/模型/策略分离；有条件适用和负例，不按知识点数量验收；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| K03 | #6 | G01, IF01 | 知识结构与理解模块专业深化 | 全域D2–D4、逐原子知识及来源定位、条件/反例、关系/组合案例、CQ及验证；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 模块完整覆盖账本，主责明确；事实/模型/策略分离；有条件适用和负例，不按知识点数量验收；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| K04 | #6 | G01, IF01 | 技能形成与迁移模块专业深化 | 全域D2–D4、逐原子知识及来源定位、条件/反例、关系/组合案例、CQ及验证；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 模块完整覆盖账本，主责明确；事实/模型/策略分离；有条件适用和负例，不按知识点数量验收；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| K05 | #6 | G01, K02, K04, IF01 | 学习策略与练习调度模块专业深化 | 全域D2–D4、逐原子知识及来源定位、条件/反例、关系/组合案例、CQ及验证；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 模块完整覆盖账本，主责明确；事实/模型/策略分离；有条件适用和负例，不按知识点数量验收；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| K06 | #6 | G01, K03, K04, IF01 | 教学设计与教学法模块专业深化 | 全域D2–D4、逐原子知识及来源定位、条件/反例、关系/组合案例、CQ及验证；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 模块完整覆盖账本，主责明确；事实/模型/策略分离；有条件适用和负例，不按知识点数量验收；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| K07 | #6 | G01, K03, K04, IF01 | 学习目标、课程与路径模块专业深化 | 全域D2–D4、逐原子知识及来源定位、条件/反例、关系/组合案例、CQ及验证；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 模块完整覆盖账本，主责明确；事实/模型/策略分离；有条件适用和负例，不按知识点数量验收；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| K08 | #6 | G01, IF01 | 动机、元认知与自我调节模块专业深化 | 全域D2–D4、逐原子知识及来源定位、条件/反例、关系/组合案例、CQ及验证；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 模块完整覆盖账本，主责明确；事实/模型/策略分离；有条件适用和负例，不按知识点数量验收；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| K09 | #6 | G01, IF01 | 教育测量与评价模块专业深化 | 全域D2–D4、逐原子知识及来源定位、条件/反例、关系/组合案例、CQ及验证；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 模块完整覆盖账本，主责明确；事实/模型/策略分离；有条件适用和负例，不按知识点数量验收；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| K10 | #6 | G01, K02, K09, IF01 | 学习者建模与知识追踪模块专业深化 | 全域D2–D4、逐原子知识及来源定位、条件/反例、关系/组合案例、CQ及验证；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 模块完整覆盖账本，主责明确；事实/模型/策略分离；有条件适用和负例，不按知识点数量验收；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| K11 | #6 | G01, K05, K08, K10, IF01 | 自适应决策与学习规划模块专业深化 | 全域D2–D4、逐原子知识及来源定位、条件/反例、关系/组合案例、CQ及验证；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 模块完整覆盖账本，主责明确；事实/模型/策略分离；有条件适用和负例，不按知识点数量验收；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| K12 | #6 | G01, K03, K06, K09, IF01 | 教学内容、练习与资源模块专业深化 | 全域D2–D4、逐原子知识及来源定位、条件/反例、关系/组合案例、CQ及验证；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 模块完整覆盖账本，主责明确；事实/模型/策略分离；有条件适用和负例，不按知识点数量验收；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| K13 | #6 | G01, IF01 | 学习环境与社会文化模块专业深化 | 全域D2–D4、逐原子知识及来源定位、条件/反例、关系/组合案例、CQ及验证；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 模块完整覆盖账本，主责明确；事实/模型/策略分离；有条件适用和负例，不按知识点数量验收；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| K14 | #6 | G01, K04, K06, IF01 | 学科与情境学习模块专业深化 | 全域D2–D4、逐原子知识及来源定位、条件/反例、关系/组合案例、CQ及验证；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 模块完整覆盖账本，主责明确；事实/模型/策略分离；有条件适用和负例，不按知识点数量验收；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| K15 | #6 | G01, K06, K09, IF01 | 教育技术与智能辅导模块专业深化 | 全域D2–D4、逐原子知识及来源定位、条件/反例、关系/组合案例、CQ及验证；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 模块完整覆盖账本，主责明确；事实/模型/策略分离；有条件适用和负例，不按知识点数量验收；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| K16 | #6 | G01, K02, K13, IF01 | 个体差异与可及性模块专业深化 | 全域D2–D4、逐原子知识及来源定位、条件/反例、关系/组合案例、CQ及验证；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 模块完整覆盖账本，主责明确；事实/模型/策略分离；有条件适用和负例，不按知识点数量验收；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| K17 | #6 | G01, IF01 | 学习研究方法与证据评价模块专业深化 | 全域D2–D4、逐原子知识及来源定位、条件/反例、关系/组合案例、CQ及验证；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 模块完整覆盖账本，主责明确；事实/模型/策略分离；有条件适用和负例，不按知识点数量验收；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| K18 | #6 | G01, K02, IF01 | 发展与学习生物基础模块专业深化 | 全域D2–D4、逐原子知识及来源定位、条件/反例、关系/组合案例、CQ及验证；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 模块完整覆盖账本，主责明确；事实/模型/策略分离；有条件适用和负例，不按知识点数量验收；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| K19 | #6 | G01, K13, K17, IF01 | 学习公平、伦理与治理模块专业深化 | 全域D2–D4、逐原子知识及来源定位、条件/反例、关系/组合案例、CQ及验证；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 模块完整覆盖账本，主责明确；事实/模型/策略分离；有条件适用和负例，不按知识点数量验收；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| KR01 | #6 | K01, K02, K03, K04 | K模块累计独立审核 K01/K02/K03/K04 | 批次内每模块独立资格收据（内容hash/消费tuple/证据/裁决），不是整批自动资格 | 逐模块exact SHA与内容身份，P0/P1关闭、P2明确处置；可审候选依赖但仅局部资格，G03验闭包；输入变化使受影响资格/消费/验证收据STALE，须重新绑定及有限复核 |
| KR02 | #6 | K05, K06, K07, K08 | K模块累计独立审核 K05/K06/K07/K08 | 批次内每模块独立资格收据（内容hash/消费tuple/证据/裁决），不是整批自动资格 | 逐模块exact SHA与内容身份，P0/P1关闭、P2明确处置；可审候选依赖但仅局部资格，G03验闭包；输入变化使受影响资格/消费/验证收据STALE，须重新绑定及有限复核 |
| KR03 | #6 | K09, K10, K11, K12 | K模块累计独立审核 K09/K10/K11/K12 | 批次内每模块独立资格收据（内容hash/消费tuple/证据/裁决），不是整批自动资格 | 逐模块exact SHA与内容身份，P0/P1关闭、P2明确处置；可审候选依赖但仅局部资格，G03验闭包；输入变化使受影响资格/消费/验证收据STALE，须重新绑定及有限复核 |
| KR04 | #6 | K13, K14, K15, K16 | K模块累计独立审核 K13/K14/K15/K16 | 批次内每模块独立资格收据（内容hash/消费tuple/证据/裁决），不是整批自动资格 | 逐模块exact SHA与内容身份，P0/P1关闭、P2明确处置；可审候选依赖但仅局部资格，G03验闭包；输入变化使受影响资格/消费/验证收据STALE，须重新绑定及有限复核 |
| KR05 | #6 | K17, K18, K19 | K模块累计独立审核 K17/K18/K19 | 批次内每模块独立资格收据（内容hash/消费tuple/证据/裁决），不是整批自动资格 | 逐模块exact SHA与内容身份，P0/P1关闭、P2明确处置；可审候选依赖但仅局部资格，G03验闭包；输入变化使受影响资格/消费/验证收据STALE，须重新绑定及有限复核 |
| H01 | #5 | G01, HSK01, IF01 | 语音与音系模块专业深化 | 声母/韵母/声调、拼音、语音规则及听辨任务；不由字形推断读音；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 完整D2–D4范围账本、来源定位/资格、原文可追溯、未解析保留；正负例与语义校验；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| H02 | #5 | G01, HSK01, HS00, IF01 | 汉字与书写系统模块专业深化 | 认读/书写等级、字符身份、构形/部件、字音及证据；不猜造部件；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 完整D2–D4范围账本、来源定位/资格、原文可追溯、未解析保留；正负例与语义校验；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| H03 | #5 | G01, HSK01, HS00, IF01 | 词汇、构词与词汇语义模块专业深化 | 11000词汇源记录保留，拼音/词性/义项按证据拆分，词义及搭配候选；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 完整D2–D4范围账本、来源定位/资格、原文可追溯、未解析保留；正负例与语义校验；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| H04 | #5 | G01, HSK01, HS00, IF01 | 语法与构式模块专业深化 | 语法源块→可核证构式与条件、正反例；不可靠分列保持HOLD；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 完整D2–D4范围账本、来源定位/资格、原文可追溯、未解析保留；正负例与语义校验；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| H05 | #5 | G01, HSK01, HS00, IF01, H03, H04 | 语用、语篇与交际模块专业深化 | 任务/话题源块→语用/语篇与场景，证据及边界；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 完整D2–D4范围账本、来源定位/资格、原文可追溯、未解析保留；正负例与语义校验；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| H06 | #5 | G01, HSK01, H01, H02, H03, H04, H05, IF01 | 语言技能与表现任务模块专业深化 | 听说读写译、技能与表现任务、标准化观测及评价；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 完整D2–D4范围账本、来源定位/资格、原文可追溯、未解析保留；正负例与语义校验；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| H07 | #5 | G01, HSK01, H02, H03, H04, H05, H06, HS00, H01, IF01 | 规范、等级与课程映射模块专业深化 | HSK版本/等级/范围、GF0025-2021与旧标准边界、能力映射；不等同先修或掌握；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 完整D2–D4范围账本、来源定位/资格、原文可追溯、未解析保留；正负例与语义校验；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| HR01 | #5 | H01, H02, H03, H04 | 汉语基础模块累计审核 | 批次内每模块独立资格收据（内容hash/消费tuple/证据/裁决），不是整批自动资格 | 逐模块exact SHA与内容身份，P0/P1关闭、P2明确处置；可审候选依赖但仅局部资格，G03验闭包；输入变化使受影响资格/消费/验证收据STALE，须重新绑定及有限复核 |
| HR02 | #5 | H05, H06, H07 | 交际、技能与标准累计审核 | 批次内每模块独立资格收据（内容hash/消费tuple/证据/裁决），不是整批自动资格 | 逐模块exact SHA与内容身份，P0/P1关闭、P2明确处置；可审候选依赖但仅局部资格，G03验闭包；输入变化使受影响资格/消费/验证收据STALE，须重新绑定及有限复核 |
| P01 | #6 | G01, DB01, K05, K06, K07, K08, K13, IF01 | 学习模式结构化模板 | 可复用模式/活动/流程或策略、条件、角色、证据、状态转移、输入输出及案例；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 声明式、可执行契约；未知/替代/停止、预算与恢复、证据独立；不将模板执行等同教育效果；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；角色/守卫/预算/停止/恢复/幂等及竞争解释负例；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| P02 | #6 | G01, DB01, K07, K08, K09, K10, K11, IF01 | 目标与学习准备结构化模板 | 可复用模式/活动/流程或策略、条件、角色、证据、状态转移、输入输出及案例；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 声明式、可执行契约；未知/替代/停止、预算与恢复、证据独立；不将模板执行等同教育效果；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；角色/守卫/预算/停止/恢复/幂等及竞争解释负例；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| P03 | #6 | G01, DB01, K03, K04, K05, K06, K12, IF01 | 学习活动单元结构化模板 | 可复用模式/活动/流程或策略、条件、角色、证据、状态转移、输入输出及案例；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 声明式、可执行契约；未知/替代/停止、预算与恢复、证据独立；不将模板执行等同教育效果；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；角色/守卫/预算/停止/恢复/幂等及竞争解释负例；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| P04 | #6 | G01, DB01, K06, K07, K11, K12, P01, P02, P03, IF01 | 学习流程结构化模板 | 可复用模式/活动/流程或策略、条件、角色、证据、状态转移、输入输出及案例；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 声明式、可执行契约；未知/替代/停止、预算与恢复、证据独立；不将模板执行等同教育效果；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；角色/守卫/预算/停止/恢复/幂等及竞争解释负例；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| P05 | #6 | G01, DB01, K02, K04, K05, K10, K11, P03, P04, IF01 | 练习与保持流程结构化模板 | 可复用模式/活动/流程或策略、条件、角色、证据、状态转移、输入输出及案例；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 声明式、可执行契约；未知/替代/停止、预算与恢复、证据独立；不将模板执行等同教育效果；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；角色/守卫/预算/停止/恢复/幂等及竞争解释负例；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| P06 | #6 | G01, DB01, K06, K09, K10, K12, P03, P04, IF01 | 观测与反馈流程结构化模板 | 可复用模式/活动/流程或策略、条件、角色、证据、状态转移、输入输出及案例；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 声明式、可执行契约；未知/替代/停止、预算与恢复、证据独立；不将模板执行等同教育效果；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；角色/守卫/预算/停止/恢复/幂等及竞争解释负例；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| P07 | #6 | G01, DB01, K08, K13, K16, K19, P02, P03, IF01 | 动机与激励流程结构化模板 | 可复用模式/活动/流程或策略、条件、角色、证据、状态转移、输入输出及案例；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 声明式、可执行契约；未知/替代/停止、预算与恢复、证据独立；不将模板执行等同教育效果；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；角色/守卫/预算/停止/恢复/幂等及竞争解释负例；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| P08 | #6 | G01, DB01, K09, K10, K11, K16, P04, P05, P06, P07, IF01 | 自适应调节流程结构化模板 | 可复用模式/活动/流程或策略、条件、角色、证据、状态转移、输入输出及案例；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 声明式、可执行契约；未知/替代/停止、预算与恢复、证据独立；不将模板执行等同教育效果；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；角色/守卫/预算/停止/恢复/幂等及竞争解释负例；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| P09 | #6 | G01, DB01, K04, K07, K09, K17, P04, P06, IF01 | 评价与迁移流程结构化模板 | 可复用模式/活动/流程或策略、条件、角色、证据、状态转移、输入输出及案例；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 声明式、可执行契约；未知/替代/停止、预算与恢复、证据独立；不将模板执行等同教育效果；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；角色/守卫/预算/停止/恢复/幂等及竞争解释负例；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| P10 | #6 | G01, DB01, K08, K11, K15, K16, K17, K19, P08, P09, IF01 | 连贯学习与治理结构化模板 | 可复用模式/活动/流程或策略、条件、角色、证据、状态转移、输入输出及案例；canonical结构化输入、D3/D4覆盖账本、精确消费引用与独立资格收据待审；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 声明式、可执行契约；未知/替代/停止、预算与恢复、证据独立；不将模板执行等同教育效果；逐D3状态/理由、源定位/命题/条件/反例/案例/验证链，四视角按适用性；数值模型独立oracle，未知HOLD；仅CANDIDATE_READY，不等同独立资格或发布；角色/守卫/预算/停止/恢复/幂等及竞争解释负例；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| PR01 | #6 | P01, P02, P03, P04, P05, P06 | 模式与流程模块累计审核 | 批次内每模块独立资格收据（内容hash/消费tuple/证据/裁决），不是整批自动资格 | 逐模块exact SHA与内容身份，P0/P1关闭、P2明确处置；可审候选依赖但仅局部资格，G03验闭包；输入变化使受影响资格/消费/验证收据STALE，须重新绑定及有限复核 |
| PR02 | #6 | P07, P08, P09, P10 | 激励、调节与长期过程累计审核 | 批次内每模块独立资格收据（内容hash/消费tuple/证据/裁决），不是整批自动资格 | 逐模块exact SHA与内容身份，P0/P1关闭、P2明确处置；可审候选依赖但仅局部资格，G03验闭包；输入变化使受影响资格/消费/验证收据STALE，须重新绑定及有限复核 |
| F01 | #6 | DB01, K03, K04, K07, K09, P02, P09, H06, H07, IF01 | 目标与能力组合契约与实例 | F覆盖索引、唯一主责引用、跨域绑定、具体输入/输出和正负例；canonical输入、逐项CQ/LC证据及消费版本；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 不复制K/H/P知识；对应CQ及LC验收；可追溯且有拒绝/未知语义；通过owner/type/version/条件校验，竞争/未知/拒绝及独立预期；不得以链接覆盖代替执行；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| F02 | #6 | DB01, K03, K04, K07, K12, P03, P04, H03, IF01, H04, H05, H06, H07 | 对象与粒度组合契约与实例 | F覆盖索引、唯一主责引用、跨域绑定、具体输入/输出和正负例；canonical输入、逐项CQ/LC证据及消费版本；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 不复制K/H/P知识；对应CQ及LC验收；可追溯且有拒绝/未知语义；通过owner/type/version/条件校验，竞争/未知/拒绝及独立预期；不得以链接覆盖代替执行；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| F03 | #6 | DB01, K06, K12, K15, K16, K19, P03, IF01, P04 | 资源与表达组合契约与实例 | F覆盖索引、唯一主责引用、跨域绑定、具体输入/输出和正负例；canonical输入、逐项CQ/LC证据及消费版本；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 不复制K/H/P知识；对应CQ及LC验收；可追溯且有拒绝/未知语义；通过owner/type/version/条件校验，竞争/未知/拒绝及独立预期；不得以链接覆盖代替执行；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| F04 | #6 | DB01, K04, K05, K06, K08, K12, K13, K15, P03, P06, IF01 | 学习交互组合契约与实例 | F覆盖索引、唯一主责引用、跨域绑定、具体输入/输出和正负例；canonical输入、逐项CQ/LC证据及消费版本；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 不复制K/H/P知识；对应CQ及LC验收；可追溯且有拒绝/未知语义；通过owner/type/version/条件校验，竞争/未知/拒绝及独立预期；不得以链接覆盖代替执行；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| F05 | #6 | DB01, K02, K03, K04, K08, K09, K10, K16, K18, P08, IF01, P10 | 学习者状态组合契约与实例 | F覆盖索引、唯一主责引用、跨域绑定、具体输入/输出和正负例；canonical输入、逐项CQ/LC证据及消费版本；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 不复制K/H/P知识；对应CQ及LC验收；可追溯且有拒绝/未知语义；通过owner/type/version/条件校验，竞争/未知/拒绝及独立预期；不得以链接覆盖代替执行；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| F06 | #6 | DB01, K02, K03, K04, K06, K09, K10, K11, K16, P06, P08, H06, IF01 | 障碍与补救组合契约与实例 | F覆盖索引、唯一主责引用、跨域绑定、具体输入/输出和正负例；canonical输入、逐项CQ/LC证据及消费版本；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 不复制K/H/P知识；对应CQ及LC验收；可追溯且有拒绝/未知语义；通过owner/type/version/条件校验，竞争/未知/拒绝及独立预期；不得以链接覆盖代替执行；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| F07 | #6 | DB01, K06, K13, K15, K16, K19, P10, IF01 | 环境与角色组合契约与实例 | F覆盖索引、唯一主责引用、跨域绑定、具体输入/输出和正负例；canonical输入、逐项CQ/LC证据及消费版本；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 不复制K/H/P知识；对应CQ及LC验收；可追溯且有拒绝/未知语义；通过owner/type/version/条件校验，竞争/未知/拒绝及独立预期；不得以链接覆盖代替执行；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| F08 | #6 | DB01, K04, K06, K07, K09, K14, K17, P05, P09, H06, IF01 | 迁移与实践组合契约与实例 | F覆盖索引、唯一主责引用、跨域绑定、具体输入/输出和正负例；canonical输入、逐项CQ/LC证据及消费版本；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 不复制K/H/P知识；对应CQ及LC验收；可追溯且有拒绝/未知语义；通过owner/type/version/条件校验，竞争/未知/拒绝及独立预期；不得以链接覆盖代替执行；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| E01 | #6 | K09, K15, K17, K19, P10, IF01 | 外部改进闭环 | 评价协议、版本、候选修订、审核与发布/回退契约；canonical输入、逐项CQ/LC证据及消费版本；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 个体观测不直接写正式库；证据/权限/版本隔离；实验效果不虚报；通过owner/type/version/条件校验，竞争/未知/拒绝及独立预期；不得以链接覆盖代替执行；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| A01 | #6 | F01, F02, IF01 | 目标→构念→知识组件贯通组合 | 绑定输入、专业规则、可判定输出、替代方案、失败案例、证据链；canonical输入、逐项CQ/LC证据及消费版本；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 真正跨域推导/决策而非仅链接；与CQ/LC一致，按需路由；通过owner/type/version/条件校验，竞争/未知/拒绝及独立预期；不得以链接覆盖代替执行；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| A02 | #6 | F02, F03, F04, IF01, H04, H05, H06 | 知识→任务→观测贯通组合 | 绑定输入、专业规则、可判定输出、替代方案、失败案例、证据链；canonical输入、逐项CQ/LC证据及消费版本；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 真正跨域推导/决策而非仅链接；与CQ/LC一致，按需路由；通过owner/type/version/条件校验，竞争/未知/拒绝及独立预期；不得以链接覆盖代替执行；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| A03 | #6 | F05, F06, IF01 | 观测→诊断→状态贯通组合 | 绑定输入、专业规则、可判定输出、替代方案、失败案例、证据链；canonical输入、逐项CQ/LC证据及消费版本；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 真正跨域推导/决策而非仅链接；与CQ/LC一致，按需路由；通过owner/type/version/条件校验，竞争/未知/拒绝及独立预期；不得以链接覆盖代替执行；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| A04 | #6 | F05, F06, P08, IF01 | 状态→策略→规划贯通组合 | 绑定输入、专业规则、可判定输出、替代方案、失败案例、证据链；canonical输入、逐项CQ/LC证据及消费版本；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 真正跨域推导/决策而非仅链接；与CQ/LC一致，按需路由；通过owner/type/version/条件校验，竞争/未知/拒绝及独立预期；不得以链接覆盖代替执行；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| A05 | #6 | F01, F08, IF01 | 教学→表现→保持/迁移贯通组合 | 绑定输入、专业规则、可判定输出、替代方案、失败案例、证据链；canonical输入、逐项CQ/LC证据及消费版本；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 真正跨域推导/决策而非仅链接；与CQ/LC一致，按需路由；通过owner/type/version/条件校验，竞争/未知/拒绝及独立预期；不得以链接覆盖代替执行；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| A06 | #6 | F03, F04, K19, IF01, H03, H04, H05 | 内容生成→核查→交付贯通组合 | 绑定输入、专业规则、可判定输出、替代方案、失败案例、证据链；canonical输入、逐项CQ/LC证据及消费版本；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 真正跨域推导/决策而非仅链接；与CQ/LC一致，按需路由；通过owner/type/version/条件校验，竞争/未知/拒绝及独立预期；不得以链接覆盖代替执行；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| A07 | #6 | F05, F07, IF01 | 环境/发展/差异→支持贯通组合 | 绑定输入、专业规则、可判定输出、替代方案、失败案例、证据链；canonical输入、逐项CQ/LC证据及消费版本；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 真正跨域推导/决策而非仅链接；与CQ/LC一致，按需路由；通过owner/type/version/条件校验，竞争/未知/拒绝及独立预期；不得以链接覆盖代替执行；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| A08 | #6 | F08, E01, IF01 | 证据→模型/政策→实证评价贯通组合 | 绑定输入、专业规则、可判定输出、替代方案、失败案例、证据链；canonical输入、逐项CQ/LC证据及消费版本；可人工阅读/审阅的UTF-8权威文本（Markdown解释与结构化JSON/JSONL记录，不重复事实） | 真正跨域推导/决策而非仅链接；与CQ/LC一致，按需路由；通过owner/type/version/条件校验，竞争/未知/拒绝及独立预期；不得以链接覆盖代替执行；结构化记录可直接校验及映射导入，不以数据库文件作为交付 |
| G03 | #6 | KR01, KR02, KR03, KR04, KR05, HR01, HR02, PR01, PR02, A01, A02, A03, A04, A05, A06, A07, A08, E01, IF01, HS00, V01, DB03 | 跨域一致性与L1冻结 | 逐模块资格收据与完整消费闭包、D3/D4和CQ覆盖账本、跨域一致性裁决及L1内容manifest | 全部计划专业模块的局部资格与确切内容hash匹配；依赖消耗tuple逐层核验、STALE拒绝；F/A/E组合独立审查；所有P0/P1关闭、P2处置；形成不可变获准内容清单；V01/DB03当前收据、逐CQ夹具及oracle身份齐全，缺失或STALE不得接受 |
| DB03 | #4 | DB02, HSK01, P04, IF01 | 文本知识包编排与导入/流程验证工具 | 全视图结构化文本包校验/清单、声明式流程验证器、可选SQLite导入器及映射、文本激活/恢复工具 | 校验所有文本/typed引用/权利/版本及独立schema；实际内存导入及语义对账、正负例、按需路由、类型关联计数；无默认SQLite文件或数据库发布包；文本包中断/回退、未实测物理跨库义务HOLD |
| V01 | #6 | DB03, F01, F02, F03, F04, F05, F06, F07, F08, E01, P10, H07, V00, A01, A02, A03, A04, A05, A06, A07, A08 | 全生命周期文本贯通切片 | 完整候选文本夹具LC01–12/CQ01–26、A01–08绑定、独立oracle与实际运行记录 | 候选文本tuple固定，HSK与最小第二学科；逐项预期/实际/负例/未运行理由，内存SQLite导入可用，影响变更重验；不替代V02 |
| G04 | #6 | G03, DB03, V01 | L2文本格式、导入与过程契约冻结 | 冻结文本schema/目录/manifest、SQLite映射及导入接口、G03获准文本清单、CQ/LC夹具与独立oracle | V01候选收据与最终冻结tuple对齐或有限重验；无陈旧引用；独立exact SHA，预期不反向修改；不要求SQLite文件 |
| V02 | #6 | G04 | 最终文本知识包与真实导入验证 | 按G03/G04精确获准文本生成版本化可读包、schema、导入工具、manifest；逐CQ/LC实际执行结果、文本/代码/schema/oracle/env hash | 实际内存SQLite导入全视图及字段/关系对账、查询计划和适用CQ/LC正负例；文本manifest回退与公私边界；不适用/实证或物理库测试HOLD有明确裁决，不冒充PASS；不发布或生成持久SQLite文件 |
| G05 | #6 | V02 | 最终文本知识包独立验收 | 独立检查实际文本包/manifest/导入器与映射，复跑关键导入及CQ/LC测试、遗留裁决 | exact SHA、文本hash、冻结tuple及资格闭包有效；P0/P1闭合、P2处置；无SQLite二进制交付，物理数据库保证未实测不得声称成立；工程与实证分离 |
| REL01 | #2 | G05 | 人类可读知识包发布裁定 | 仅G05批准且合法的可读文本包、schema、导入工具、manifest、验证报告、版本及回退说明 | 批准文本bytes/hash、权限/权利、历史版本保留、文本包恢复验证；不激活候选/私有数据，不分发.sqlite/.db；#2–#6记录一致 |
| IF01 | #6 | S01, DB01, G01 | 早期共同语义接口 | 版本化F/P/A共享对象/角色/目标/观测/状态/类型与结构化创作交换合同；候选样例与验证规则 | K/H/P/F/A/E共同引用，源→定位→命题→实体/关系→案例→验证的稳定ID、类型、条件、版本；错误类型/悬空引用/未知拒绝；非G04最终冻结 |
| HS00 | #5 | S01, SRC01 | HSK标准与来源记录早期接口 | 版本、来源记录身份、级别原串/合并级别、源页序号、字符与词汇源记录区别、字段解析边界 | 先于H模块形成候选接口；原PDF/权利未知HOLD；H07最终标准映射仍须完整专业证据 |
| V00 | #6 | DB02, IF01 | 有限文本原型与导入可行性 | 原创/合成可读夹具、接口、内存SQLite导入/流程原型、预期与失败记录 | 只验证有限文本和导入契约；不生成持久SQLite，不替代V01/V02；不晋升专业知识 |

## 拓扑波次
1. S01 / DB01 / SRC01
2. G01 / DB02 / HS00
3. IF01
4. HSK01 / K01 / K02 / K03 / K04 / K08 / K09 / K13 / K17 / V00
5. K05 / K06 / K07 / K10 / K16 / K18 / K19 / KR01 / H01 / H02 / H03 / H04
6. K11 / K12 / K14 / K15 / KR02 / KR05 / H05 / HR01 / P01
7. KR03 / KR04 / H06 / P02 / P03
8. H07 / P04 / P07
9. HR02 / P05 / P06 / F02 / F03 / DB03
10. P08 / P09 / PR01 / F04
11. P10 / F01 / F06 / F08 / A02 / A06
12. PR02 / F05 / F07 / E01 / A01 / A05
13. A03 / A04 / A07 / A08
14. V01
15. G03
16. G04
17. V02
18. G05
19. REL01

初始S01/DB01/SRC01允许正式执行；其余按当前有效收据解锁。SRC01仍PARTIAL，HS00/HSK01等待。

## 当前调度状态（S01-FORMAL-01）
S01 CANDIDATE_READY（正式范围候选收据）；G01 READY（待独立范围裁定）；DB01 READY（正式设计）；SRC01 BLOCKED（已保全的部分证据，尚不签PRESERVATION_VERIFIED）。其他任务均PLANNED，G03/G04/G05未运行。

## G01 / DB01 当前收据
G01 GATE_ACCEPTED（独立范围）；DB01 CANDIDATE_READY（39类候选格式与映射）；IF01/DB02 READY；SRC01 BLOCKED。其余按收据解锁，不提前晋升。

## IF01当前收据
IF01 CANDIDATE_READY，首批K01/K02/K03/K04/K08/K09/K13/K17与DB02可执行；SRC01仍BLOCKED。专业任务不得凭历史候选数目自动晋升。

## K01–K04 首批正式专业候选
K01–K04 CANDIDATE_READY，KR01 READY（逐模块资格裁定）；新增可执行任务：K05, K06, K07, K18, KR01。原源定位与专业充分性缺口保留，不提前晋升。

### KR01 R2 candidate update

KR01 original independent result REWORK_REQUIRED (comment 7213482417; 6 P1, 2 P2). K01–K04 FORMAL-02 receipts are current, with artifact 322e487f37b1de33042a3f3f2bc7b72f4b5503c6. FORMAL-01 remains historical, not a current consumption tuple. No existing dependent consumption receipt found; future tasks bind the new tuples. KR01 remains READY for a scoped RV01–RV08 independent delta review; qualifications NOT_RUN.

### KR01 R3 residual candidate

R2 independent comment 7214381381: K01/K02/K04 ACCEPT_SCOPED; K03 residual P1 R2-RV04-01, K02 nonblocking P2 R2-RV07-01. R3 artifact 4b35b500aaccac4787c6fb68fa950199ac34a760 preserves prior 53 checks, adds 19; exact GitHub replay clean. All four FORMAL-03 candidate receipts bind new shared version; normalized K01/K04 unchanged. Independent residual review and current tuple rebind still required, no full repeated review. Other READY tasks remain eligible under contract; no downstream issued receipt, SRC01 still BLOCKED.

### KR01 closeout

Independent ACCEPT_SCOPED #6 comment 7214923937 / #2 7214924825, exact HEAD 607a21b9133cdc1bbc1cd45cba5d8f7bf5b06c1b. K01–K04 local qualification receipts registered separately, current FORMAL-03 candidate consumption unchanged. KR01 QUALIFICATION_RECEIPTS (8/8 original, two residual closed, P0/P1/P2=0). Local scope only; K01 optional HOLD, rights, G03 closure, CQ/LC, release remain unapproved.

### DB02 scoped candidate

DB02 CANDIDATE_READY (FORMAL-01; 33/33 builder tests, 38 record kinds, exact replay); V00 READY. Candidate research only, no persistent SQLite or release/approval authority.

### V00 finite prototype

V00 CANDIDATE_READY (FORMAL-01; 12/12 synthetic flow cases, byte-identical exact replay, DB02 33/33). No CQ/LC, learner or final qualification. V01 waits for remaining receipts.

## 2026-11-27 — KR03/KR04/KR05 restricted candidate registration

Independent batch review #6 comment 7221120084 accepted the exact 62760bfd4690279cf2a703be8cc908a92ef1d755 / tree 0a2970ec606210ff98eb475906c7ffea168ab22e scope: 115/115 new finite oracles, 36/36 exact bindings, 27/28 input-determined cross-compositions, and restricted candidate readiness recommended for K09/K13/K14/K17/K18. No qualification was issued by that review.

After exact branch/head/tree/CAS and prerequisite-receipt checks, registered:
- K09 evidence/tasks/K09/K09-FORMAL-01.json — CANDIDATE_READY, restricted; 75 candidate claims / 60 HOLD.
- K13 evidence/tasks/K13/K13-FORMAL-01.json — CANDIDATE_READY, restricted; 45 candidate claims / 35 HOLD.
- K14 evidence/tasks/K14/K14-FORMAL-01.json — CANDIDATE_READY, restricted; 48 candidate claims / 40 HOLD; K06 consumption remains restricted.
- K17 evidence/tasks/K17/K17-FORMAL-01.json — CANDIDATE_READY, restricted; 67 candidate claims / 44 HOLD.
- K18 evidence/tasks/K18/K18-FORMAL-01.json — CANDIDATE_READY, restricted; 42 candidate claims / 25 HOLD.

The five receipts pin exact current direct-dependency receipts and qualifications, module/package manifests, JSONL shards, coverage, bounded source/depth material and the review's scope ledger. Their content digests cover canonical input/output tuples. This is candidate registration only: no QUALIFIED_LOCAL receipt, no source-rights clearance, no CQ/LC, no held-claim promotion, no G03 or release. K10/K11/K12/K15/K16/K19 remain preparation-only pending their exact formal prerequisites. The two P2 findings and one P3 source-pinning limitation remain open.

## 2026-11-27 — KR03–KR05 P2 builder remediation

The two P2 findings from independent review #6 comment 7221120084 now have bounded builder-side remediation in the current branch: P2-01 uses a shared versioned ModelSpec parameter-domain guard (7/7 explicit fixtures, 4/4 unit tests); P2-02 makes X01 self-contained and adds strict fail-closed cross-adapter domains (41/41 fixtures, 36 exact bindings). Both remain PENDING_INDEPENDENT_DELTA_REVIEW. P3-01 source-version/authority pinning remains OPEN. No qualification, source-rights, CQ/LC, G03 or release state is promoted. Details and hashes are recorded in docs/implementation/kr03-05-batch/p2-remediation.md and the K10/K12 validation/consumption receipts.

## P01 bounded learning-mode candidate

P01 six learner-selected templates, 182 process records, 24 activities, six flows, 36 builder guard cases (six common patterns across six mode identities). 121 upstream applicability rows: 29 direct / 92 indirect, not professional adequacy. Exact scope and typed references, in-memory import passed. Current P01 restricted candidate receipt binds the artifact at 479853eb58c769551131a6ac6266b3083adf9cad. No independent qualification; actual mode-specific flow execution and broader composition remain pending.
