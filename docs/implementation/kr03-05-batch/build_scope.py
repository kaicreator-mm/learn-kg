"""Freeze prospective review inputs, no task-state advancement."""
from check_cross import *
def main():
 d=load(ROOT/'docs/implementation/task-dag.json');tasks={t['id']:t for t in d['tasks']}
 result=[]
 for i in range(9,20):
  k=f'K{i:02}';p=B/owners[k];c=load(p/k/'coverage.json');m=load(p/'learning-core.manifest.json');r={}
  for e in c['record_files']:
   f=p/e['path'];assert sha(f)==e['sha256']
   for l in f.read_text().splitlines():
    x=json.loads(l);r[x['stable_id']]=x
  views=[];topic_rows=[]
  for t in c['topics']:
   ids=t['claim_ids'];assert all(x in r for x in ids)
   active=[x for x in ids if r[x]['status']=='CANDIDATE'];assert set(active)==set(t['active_claim_ids'])
   # Preserve exact source metadata instead of inferring verification from nomenclature.
   for cid,refs in t['explicit_view_claim_refs'].items():
    for ref in refs:views.append({'topic':t['d3_id'],'claim_id':cid,'claim_status':r[cid]['status'],'view':ref,'disposition':'HOLD_ORIGINAL_CLAIM_NOT_ACTIVE' if r[cid]['status']!='CANDIDATE' else 'ACTIVE_BINDING_APPLICABILITY_REVIEW_PENDING'})
   topic_rows.append({'topic':t['d3_id'],'active_claim_ids':active,'hold_claim_ids':[x for x in ids if r[x]['status']=='HOLD'],'view_scope_refs':t['view_scope_refs'],'actual_source_statuses':{x:r[x].get('source_status') for x in ids},'validation_ids':t['validation_ids']})
  dep=[]
  for a in tasks[k]['depends_on']:
   t=tasks[a];rec=t.get('current_receipt');q=t.get('qualification_receipt')
   x={'task':a,'state':t['status']}
   if rec:
    rr=load(ROOT/rec);x.update(receipt=rec,receipt_sha256=sha(ROOT/rec),content_digest=rr['content_digest'])
    if q:
     qr=load(ROOT/q);assert qr['reviewed_content_digest']==rr['content_digest'];x.update(qualification=q,qualification_sha256=sha(ROOT/q),scope=t.get('qualification_scope','LOCAL'))
   else:x['disposition']='MISSING_CURRENT_FORMAL_RECEIPT'
   dep.append(x)
  result.append({'owner':k,'task_state':tasks[k]['status'],'snapshot':owners[k],'version':m['version'],'manifest_sha256':sha(p/'learning-core.manifest.json'),'coverage_sha256':sha(p/k/'coverage.json'),'topics':len(topic_rows),'records':len(r),'topic_rows':topic_rows,'view_obligations':views,'dependencies':dep,'disposition':'REVIEW_RESTRICTED_READINESS_ONLY' if tasks[k]['status']=='READY' else 'PREPARATION_ONLY_MISSING_FORMAL_INPUT'})
 out={'status':'PREPARATION_SCOPE_REVIEW_ONLY','modules':result,'limits':'No source status promotion, replacement of held view binding, CQ/LC verdict or actual candidate receipt. Reviewer must judge source depth and applicability; missing formal inputs block promotion.'}
 (P/'scope-ledger.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print('modules',len(result),'topics',sum(x['topics'] for x in result),'view obligations',sum(len(x['view_obligations']) for x in result),'held views',sum(v['disposition'].startswith('HOLD') for x in result for v in x['view_obligations']))
 for x in result:print(x['owner'],x['task_state'],x['topics'],len(x['view_obligations']))
if __name__=='__main__':main()
