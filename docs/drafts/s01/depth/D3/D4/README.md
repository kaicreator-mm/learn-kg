# D4 — 可读知识包与 SQLite 最小导入投影

基线 c53d10f77b77c813233994f3fd9814b5fc20ccde；测试精确 HEAD c7ad4d97bfb8d174319437aff0241bbcd6387509。调查草案，不发 DB01/DB02/IF01 或 G01/G03 正式收据，不冻结正式 schema。

## 权威文本与包
沿用 D014 和 DB01 调查设计。manifest.json 以4个逻辑包引用253份既有或本批JSON文本，每项记录相对路径、类型、Git Blob、SHA256；依赖按精确版本和包清单摘要绑定。清单的 base 是旧知识基线，新增 flow-candidate.json 由自己的文件hash绑定，不声称该新文件已存在于base。现有专业 Markdown/JSON仍是知识唯一事实源，不另复制1712条命题。learning-core包含K19域；chinese包含H7域；learning-process依赖core，按通用契约组织；research-overlay依赖三个包，供建设者完整对账。逻辑包不是实际四个SQLite文件，不改变正式包主责。

## 导入与动态过程
project.py 使用Python标准库、严格重复key拒绝、文件hash、包摘要、版本依赖、端点身份；SQLite 仅 :memory:，registry与专业投影列分离，原记录payload保留以验证无损往返。映射表为modules/topics/sources/claims/cases/contracts/flows/flow_steps/flow_guards/flow_transitions/relation_types/edges/held_anchors/overlays。文本引用映射为带类型边，SQL触发器与FK拒绝错误端点；题目/案例和来源记录不晋升专业资格。189条历史研究锚点全部独立隔离（15范围外），20条语义候选不自动物化为已接受边，保留364深化、974记录引用及100契约命题引用。2项来源校准附记仍非外部字节资格。
flow-candidate.json 新增1个通用学习循环、10步、9守卫、9转移、全局退出优先、失败/未知暂停、轮次及时间预算、激励选择；仅声明式含义和契约引用，不是生产执行代码。RETENTION只安排复测，不能声称已保持。未用一个模板替代27项合同全部流程。

## 实际最小验证
SQLite 3.45.1，4个按需路由（core172文件；chinese74；process175；完整overlay253），完整视图26模块、648主题、1712命题、441来源、648案例、27契约、5931类型候选/结构/记录边，3476条主题/命题/来源/案例/契约payload实际往返一致，流程payload另核。29项固定检查通过，含外键、类型、孤儿、重复ID、错版本/缺包、hash篡改、重复JSON键、流程守卫孤儿、查询及EXPLAIN覆盖索引。初次流程增量写入出现重复DDL定义而失败，去重后重新生成manifest并执行；无失败结果伪报。
从精确HEAD新checkout，实际 python3 -m py_compile、重新生成manifest与receipt，二者cmp完全相同；本目录无持久.sqlite/.db/.sqlite3文件。运行：python3 docs/drafts/s01/depth/D3/D4/project.py 。manifest生成模式仅用于候选构建，不是独立签名或正式发布。
SHA256: flow-candidate.json 91d208dc00c557154e2874a8abe5db3a3ade8316e1287a82b45da545292bb35c; project.py afb62c8abbab7f7075745517ba23ca2e422ca7bfd33cdc6b6cb82ce421156a75; manifest.json f5004557ea7f8d110b632336c225888e4797654c6186227d6ad29497a845b365; receipt.json d10cbd6f0b2c87a7f4034ce0bc605b5278fdd89318057fbd22121a3a6e5fcc72。

## 未完成及下一步
仅候选研究投影，结构核验非专业正确性；同作者固定断言，非独立oracle。未迁移私有HSK词表/字符/等级成员、未重核历史来源字节/权利、未导入模型试点全部专业字段与深层关系、未冻结JSON schema及跨包resolver正式合同、未做物理多库/性能/崩溃/发布/真实学习者状态。当前映射以全局稳定ID和包级hash为有限约定，非完整跨包typed ref/签名/权限系统；未知字段不是正式schema接受。没有覆盖全部知识组合的实际专业推理，364深化命题仍未全量绑定27契约。保持正式DAG门禁；下一步应进行累计独立审核，先核S01范围/候选内容、DB01设计及动态组合可读表达，区分正式范围门禁、专业资格和导入工具验收，不直接宣告G03或DB02完成。
