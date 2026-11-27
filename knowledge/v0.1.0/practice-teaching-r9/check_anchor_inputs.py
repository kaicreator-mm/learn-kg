"""Bind exact prerequisites and reconcile preserved D4 requirements; not graph qualification."""
import check_cross_inputs as c
from collections import Counter
P=c.P; ROOT=c.ROOT
design=[
 dict(id='XA01',owner='K05',local='K05.01.01.PT.01',upstream='K02.06.01.D4.01',use='设计提取练习时记录提示与竞争线索；比较时控制提示条件。',boundary='策略差异不能证明线索机制唯一成立。'),
 dict(id='XA02',owner='K07',local='K07.01.02.PT.01',upstream='K03.02.01.D4.03',use='知识维度与过程维度独立记录，同一任务可有多标签。',boundary='多维项目规则不构成Bloom分类的外部实证。'),
 dict(id='XA03',owner='K07',local='K07.03.03.PT.01',upstream='K04.06.03.D4.01',use='路径比较要求匹配目标并增加独立陌生情境观察。',boundary='多情境学习不保证任意迁移或路径等效。')]
out=[c.resolve(x) for x in design]
bind=dict(zip(['K05-L1','K07-L1','K07-L7'],out,strict=True))
a=c.load(P/'anchor-dispositions.json')
scope=ROOT/'docs/drafts/s01-scope-inventory.json'
samples=c.load(scope)['existing_d4_samples']
qd=[]
for row in a['rows']:
 if row['id'] in bind:
  w=bind[row['id']]
  c.need(row['original']['from']+'.PT.01'==w['local']['stable_id'] and row['original']['target']==w['upstream']['owner'],'historical endpoint')
  row.update(disposition='BOUND_DECLARED_INPUT_SEMANTIC_USE_PROPOSED',witness_ids=[w['id']],next='Professional adequacy review; not a qualified graph relation.')
 elif row['id'] in ('K05-L4','K05-L5'):
  j,s=next((i,s) for i,s in enumerate(samples) if s['id']==row['original']['target'])
  local=s['d3_id']+'.PT.01';x,f,e=c.li[local]
  c.need(s['d3_id']==row['original']['from'] and x['owner']==row['owner'],'sample mismatch')
  w=dict(id=s['id'],source_path=scope.relative_to(ROOT).as_posix(),source_sha256=c.sha(scope),pointer=f'/existing_d4_samples/{j}',sample=s,local=local,record_sha256=c.digest(x),local_file=f.relative_to(ROOT).as_posix(),local_file_sha256=e['sha256'],status='PRESERVED_REQUIREMENT_RECONCILED_NOT_EMPIRICAL_QUALIFICATION')
  qd.append(w)
  row.update(disposition='PRESERVED_D4_SAMPLE_RECONCILED',witness_ids=[s['id']],next='Review whether the method and independent finite fixtures meet the original boundary; no graph edge inferred.')
a['counts']=dict(Counter(x['disposition'] for x in a['rows']))
c.need(len(a['rows'])==56 and len(qd)==2 and len(out)==3,'coverage')
c.need(not any(x['disposition'] in ('DECLARED_INPUT_TOPIC_BINDING_HOLD','HISTORICAL_REFERENCE_RECONCILIATION_HOLD') for x in a['rows']),'remaining identity gaps')
def save(p,x):p.write_text(c.json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
save(P/'anchor-dispositions.json',a)
save(P/'anchor-input-witness.json',dict(status='BOUNDED_IDENTITY_ONLY',pairs=out,d4_samples=qd,limits='No new task dependency or graph qualification. Forty-seven later integration obligations remain.'))
print('ANCHORS',a['counts'])
