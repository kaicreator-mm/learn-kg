"""Original scalar formula representations. Applicability is mandatory, not inferred from AST."""
import json,pathlib
P=pathlib.Path(__file__).resolve().parent
def V(x):return {'variable':x}
def C(x):return {'constant':x}
def O(op,*a):return {'op':op,'args':[V(x) if isinstance(x,str) else C(x) if type(x) in (int,float) else x for x in a]}
def add(*a):return O('add',*a)
def sub(a,b):return O('sub',a,b)
def mul(*a):return O('mul',*a)
def div(a,b):return O('div',a,b)
def pow_(a,b):return O('pow',a,b)
def logistic(x):return div(1,add(1,O('exp',O('neg',x))))
def p(name,unit,meaning,lo=None,hi=None):return dict(name=name,unit=unit,meaning=meaning,lower=lo,upper=hi)
def prob(name,meaning):return p(name,'probability',meaning,0,1)
def count(name,meaning):return p(name,'count',meaning,0,None)
def free(name,meaning):return p(name,'declared scale',meaning)
def F(name,x):return dict(name=name,expr=x)
rows=[]
def model(topic,label,definition,params,formulas,app,boundary,domain='RATIONAL'):
 rows.append(dict(topic='K09.'+topic,id='K09.'+topic+'.MODEL.01',label=label,definition=definition,parameters=params,formulas=formulas,applicability=app,boundary=boundary,numeric_domain=domain))
model('02.02','经典测量信度','指定重复测量程序的方差比例',[p('true_var','score squared','真分数方差',0),p('error_var','score squared','误差方差',0)],[F('reliability',div('true_var',add('true_var','error_var')))],['同一总体和重复测量程序','误差均值0且与真分数不相关；总方差>0'],'信度非效度；不得把不同重复条件的信度互换。')
model('03.01','有效作答正确率','样本内正确率及缺答率',[count('correct','正确'),count('incorrect','错误'),count('missing','缺答')],[F('p',div('correct',add('correct','incorrect'))),F('missing_rate',div('missing',add('correct','incorrect','missing')))],['各计数非负整数','有效作答及总数均>0；缺答单列'],'不将样本正确率当IRT位置参数。')
model('03.02','高低组正确率差','同题两个定义明确组的正确率差',[count('hi_correct','高组正确'),count('hi_total','高组有效总数'),count('lo_correct','低组正确'),count('lo_total','低组有效总数')],[F('difference',sub(div('hi_correct','hi_total'),div('lo_correct','lo_total')))],['两组分母>0且正确数不超过总数','组定义及抽样条件明确'],'不是点二列相关或IRT斜率。')
model('03.04','经典测量标准误','同一量尺和总体的平均SEM',[p('sd','score','观测分标准差',0),prob('r','对应信度')],[F('sem',mul('sd',pow_(sub(1,'r'),0.5)))],['SD与r同一总体和量尺；误差模型适用'],'不是个体置信区间；条件SEM另估。','BINARY64')
model('04.01','二分Rasch概率','D=1且固定斜率1的条件响应概率',[free('theta','潜在位置'),free('b','题目位置')],[F('p',logistic(sub('theta','b')))],['同尺度且参数有限，固定斜率1','二分响应；模型拟合与识别另证'],'全对全错不填有限无约束MLE；非实际能力诊断。','BINARY64')
model('04.02','二分3PL概率','D=1的下渐近参数与logistic响应概率',[free('theta','潜在位置'),free('b','题目位置'),p('a','inverse latent scale','正斜率',0),prob('c','下渐近参数')],[F('p',add('c',mul(sub(1,'c'),logistic(mul('a',sub('theta','b'))))))],['a>0、0<=c<1；同一识别尺度','有限参数、二分模型；c=0退化2PL'],'c不是某次实际猜测事件；概率正确不证实模型拟合。','BINARY64')
model('04.03','二维补偿性logit','两维度固定参数的补偿性概率',[free('a1','维1负荷'),free('a2','维2负荷'),free('theta1','维1位置'),free('theta2','维2位置'),free('d','截距')],[F('p',logistic(add(mul('a1','theta1'),mul('a2','theta2'),'d')))],['仅此二维补偿模型；同尺度；有限参数'],'相同logit不证明画像相同；非补偿模型另定义。','BINARY64')
model('04.04','2PL单题信息','D=1的2PL条件信息',[p('a_squared','inverse latent scale squared','斜率平方',0),prob('p','条件正确概率')],[F('information',mul('a_squared','p',sub(1,'p')))],['a_squared>0；0<p<1','局部独立才可相加；总信息>0才可求条件SE'],'无局部独立不能直接相加；模型条件精度非真实学习效果。')
eta=mul(sub(1,mul('q1',sub(1,'alpha1'))),sub(1,mul('q2',sub(1,'alpha2'))))
model('05.01','二属性DINA有限形式','两个二元属性与非空Q行的合取理想响应',[prob('q1','是否需属性1'),prob('q2','是否需属性2'),prob('alpha1','属性1画像'),prob('alpha2','属性2画像'),prob('s','滑失'),prob('g','猜测')],[F('eta',eta),F('p',add('g',mul(sub(sub(1,'s'),'g'),eta)))],['q及alpha仅0/1；至少一项q=1','1-s>g，参数在[0,1]；固定Q行'],'不是后验掌握概率；更高维须显式扩展。')
model('07.03','筛查混淆矩阵指标','适用参考标准下的二分类比例',[count('tp','真阳性'),count('fn','假阴性'),count('tn','真阴性'),count('fp','假阳性')],[F('se',div('tp',add('tp','fn'))),F('sp',div('tn',add('tn','fp'))),F('ppv',div('tp',add('tp','fp')))],['参考标准适用；四计数非负整数；各分母>0'],'预测值依目标总体基率；筛查阳性非确诊或自动能力分类。')
model('07.04','线性尺度链接','匹配均值标准差的线性映射',[free('mux','X均值'),p('sx','X score','X标准差',0),free('muy','Y均值'),p('sy','Y score','Y标准差',0),free('x','X分数')],[F('linked',add('muy',div(mul(sub('x','mux'),'sy'),'sx')))],['同目标总体及可比设计；sx,sy>0'],'线性链接不等于等值或个体回归预测。')
(P/'model-design.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
