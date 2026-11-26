# DB01 可读知识统一表达调查原型
基线 3bae04c5fe5871f22c3a12c415ddc520a51dbeed；沿用D014，原BKT/HLR记录及证据不修改。统一schema draft-unified-1；65条原记录按稳定ID转换，三逻辑测试包：BKT、HLR模型、复习策略/跨模块验证。后者依赖HLR，依赖以目标包ID、版本、内容SHA256绑定。此分拆只用于跨包解析验证，不决定正式物理库或专业主责。K10验证规格含K10/K11案例，放在review测试包避免反向依赖，仍保留原owner。统一Source.identifier、Case.target_ref与mode、ModelSpec.numeric_domain/input_policy；不覆盖原来源资格，不丢原字段。保持原模型公式、条件、限制、案例预期；运行期统一求值器/有限策略解释及SQLite内存映射另见验证脚本。所有候选均DRAFT，原验证规格NOT_RUN；既有证据不随格式变化自动晋升。仅调查原型，不冻结IF01/DB01、完成DB02或公开受限源，不生成SQLite文件。
 
[统一schema](schema.json) / [manifest](manifest.json) / [BKT](bkt.json) / [HLR](hlr.json) / [复习策略及组合验证](review.json)。正式实施门禁仍HOLD。

## 实际验证
测试HEAD 2adc03a1f939fae1231e439f26b19c58d9a413b9，Gateway job_01M8C0Y3A100Q8HW2AHW4VQ235 exit0；6个Git Blob核对、py_compile通过。65条原记录逆转换逐字段一致；35/35原案例、5/5模型→策略组合、16/16文本/引用负例、3/3 SQL负例通过。3个文本包按需路由：BKT仅bkt.json，review仅hlr.json+review.json。SQLite 3.45.1 只使用单个 :memory: 连接，9类记录表+registry+refs，65/65记录与189/189引用往返对账，外键检查通过。通过实际SQL查询找回review策略→HLR模型引用。运行目录检查无.db/.sqlite/.sqlite3文件。首次HEAD edcc64... 的DDL字符串语法错误，exit1未执行测试，修正并加固非空键后重跑；历史失败保留。[完整证据](validation-evidence.json)。

## 限制
共享schema和AST执行仅覆盖两个试点与有限策略规则；适配器仍显式处理模型的输入/流程。SQL嵌套属性按字段JSON保存，不是完整专业DDL；只证明本试点内存投影可导入性，未证明实际多库路由、性能、持久文件、崩溃恢复或正式SQLite导入器。预期由Builder编写，未独立审核；正式资格、参数校准、真实学习效果及完整CQ06/07/25/26均NOT_RUN。没有生成SQLite文件、不晋升任务。

## V2语言实体与有界活动扩展（调查）
原三包与65条记录保持字节不变，历史验证证据保留。共享schema扩展8种类型：HanCharacter、Reading、Lexeme、Sense、ConditionSpec、TaskSpec、FlowSpec、ScenarioCase。新增chinese 31条、flow 17条，flow声明chinese依赖；新语义是小范围辞书候选，不是全HSK知识或正式迁移。汉典“买”“卖”条已读HTML，见来源与定位。条件关系仅同笔已完成的货物金钱交易、角色匹配时成立；未知条件保留UNKNOWN，不推断实际交易。原创书面辨义任务不等同听辨；活动完成不等于掌握。有限事件预算、独立性、权限、任务身份、重复事件、退出和终止；不实现真实运行时、持续学习者状态或独立效果。V2记录及schema为调查候选；实际验证证据另附，不改写V1证据。