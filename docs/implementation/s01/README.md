# S01 — 正式范围候选交付
D013 R3-R 独立规划通过后，采用已存在的累计候选材料作为范围输入，不重复专业正文。S01只产出CANDIDATE_READY；G01独立范围审核尚未完成，所有专业资格、CQ和LC均NOT_RUN。
- [正式范围候选清单](scope-candidate.json) 是消费入口：逐模块/视图的主责、资格路径、范围与来源缺口、16个必需模块字段的解码/绑定和完整输入hash。
- [原分类库存](../../drafts/s01-scope-inventory.json) 823节点；[逐D3/D4覆盖清单](../../drafts/stage-handoff/qualification-preparation/ledger-manifest.json) 648主题、1743保留候选记录（1740当前消费、3历史替代）；299个原输入及13分片。旧状态不视为当前调度或专业资格。
- [过程/组合与CQ/LC账本](../../drafts/stage-handoff/qualification-preparation/views-cq-relations.json) 27视图108要求、26 CQ、12 LC。未声明绑定与未核证定位不擅自推导；范围未省略，不等同充分性。
- [HSK归档映射](../../drafts/s01/hsk-source-domain-mapping.json) 是范围和来源字段计划；[原件保全](../../drafts/stage-handoff/qualification-preparation/src01-original-pdf-backup-evidence.json) 已有当前原件身份/字节恢复，历史差异及权利仍HOLD；不得以S01解锁HS00。
- 执行 `python3 docs/implementation/s01/verify_scope.py` 在完整Git工作树校验并生成相同清单（禁止 -O）；此前映射见证独立于本范围收据、仅同作者静态验证。以实际G01裁定决定范围，不以数量或历史脚本通过替代专业资格。
