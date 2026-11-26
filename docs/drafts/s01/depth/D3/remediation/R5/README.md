# R5 — RV01/RV02 残留限定修正
独立R4 review comment 7203292140，基线 2b97ea136d2c0117e3a864ec423330d6c0d71b7a，TREE 9aef62cc666de68420ab55b24bb28f0f69c4b9f1。R4 5/7 ACCEPT_SCOPED（RV03–07），2/7 REWORK_REQUIRED（RV01、RV02.a/.b），不重开已认可范围。仅增量候选修正，不发正式资格收据。
## RV01
depth-disposition.json 以原327逐主题筛查为基线，明确12高风险主题（9原generic-retained、2原应用HOLD、1原补充）44需求侧面，21候选实例、19部分支持、4 HOLD，逐侧面有同主题原/新claim及实际案例路径/理由。覆盖K06.03.01–04、K09.01.01–04、K12.03.02–04、K12.05.04。189通用理由保留项中的另外180逐ID改为 RETAIN_PENDING_PROFESSIONAL_ADEQUACY_NOT_ASSESSED。旧R2 triage不改；90应用/来源HOLD、22政策或专业边界、26补充原计数保持，不加总重复覆盖。既不认定327充分，也不机械新增命题。实际校准、完整开放评分、专业资格留后续。
## RV02.a/b
contracts.json 明确有限数学评分/暴露边界。两种方法必须有精确算术、方法对应布尔断言与受控规范解释；已知矛盾或错误断言/计算为0，未知开放解释为null/人工，不能用“正”或“单位”子串判断。正数关系正确与理由正确分别记录。允许非最小公分母及两种合法方法；数轴等未支持方法不自动判错。四个旧正例新增合成结构化断言（fixtures.json），非从未知真实响应推断。
对两个学科，明确目标ID、内容签名和有限TARGET标记；与related=false矛盾或PREVIEW_TARGET身份冲突HOLD；相关或其他同构念观测与基线/目标同分钟没有可靠顺序HOLD；只有严格早于响应的已知相关事件才用于最后暴露计算；真实无关事件不阻断、确定响应后事件不计作之前练习。保留全部旧正负及HOLD条件。未知历史/合法性HOLD，不声称真实全量日志、语义近重复识别或因果效果。
requirement-corrections.json 14条原映射逐ID保留旧状态及理由，修正P05/P09/A02/A03/A05受影响要求为PARTIAL；合并视图108条=61 EXEMPLIFIED/37 PARTIAL/10 HOLD，均非正式验收。
## 最小验证
probe.py 依赖既有R3固定夹具/旧score与classify，用原始函数实际复现两个理由错误放行与两学科各四个历史错误放行（10），新17理由情形及32双科历史情形均通过；旧14评分、30历史情形重放通过；原189保留项闭合、12侧面路径与claim身份、14映射修正/108总数核对。无持久SQLite。receipt.json 是实际同作者固定预期运行输出，非独立oracle。旧R3文件、历史收据/清单保持原快照，下一轮消费必须按R5/contracts+fixtures+probe及depth-disposition/requirement-corrections覆盖对应旧候选解释，不能再直接使用旧R3判定函数作为当前结论。未更新正式schema、HSK/SRC01或正式DAG，CQ26 NOT_RUN。下一步仅RV01残留筛查和RV02.a/.b独立限定复审。
