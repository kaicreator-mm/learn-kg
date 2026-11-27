"""Read-only source and topic inventory for KR02; not qualification."""
import collections, hashlib, json, pathlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
Q=ROOT/'docs/drafts/stage-handoff/qualification-preparation'
MODS=('K05','K06','K07','K08')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
m=read(Q/'ledger-manifest.json')
inputs=[];data={}
def at(ref):
 i,ptr=ref;f=m['files'][i];p=ROOT/f['path']
 if i not in data:
  assert sha(p)==f['sha256'],str(p);data[i]=read(p)
  inputs.append(dict(path=f['path'],sha256=f['sha256']))
 x=data[i]
 for k in ptr[1:].split('/'):x=x[int(k)] if isinstance(x,list) else x[k.replace('~1','/').replace('~0','~')]
 return x
checks={}
for line in (P/'source-checks.tsv').read_text().splitlines():
 c,s,url,loc,mode,note=line.split('|')
 assert (c,s) not in checks
 checks[c,s]=dict(url=url,locator=loc,mode=mode,support_and_limits=note,qualification='NOT_RUN')
rows=[]
for sh in m['shards']:
 p=Q/sh['file'];assert sha(p)==sh['sha256']
 for line in p.read_text().splitlines():
  t=dict(zip(m['topic_columns'],json.loads(line),strict=True))
  if t['owner'] not in MODS:continue
  req=at(t['requirement_ref'])
  cands=[]
  for raw in t['claims']:
   c=dict(zip(m['claim_columns'],raw,strict=True));rec=at(c['record'])
   src=[]
   for row in c['source_refs']:
    sid,sref,field,location,access,rights=row;s=at(sref)
    key=c['id'],sid
    src.append(dict(source_id=sid,source_title=s['title'],historical_url=s.get('url'),historical_location=rec.get(field) if field else None,historical_location_status=location,historical_access=access,rights=rights,recheck=checks.get(key),disposition='NEW_LOCATOR_CANDIDATE_LIMITED' if key in checks else 'REVIEW_REQUIRED_LOCATOR_MISSING' if 'MISSING' in location else 'REVIEW_REQUIRED_HISTORICAL_LOCATOR'))
   cands.append(dict(claim_id=c['id'],claim_type=c['claim_type'],statement=rec.get('claim',rec.get('statement')),source_status=c['source_status'],source_associations=src,claim_pointer=c['record'],case_refs=c['case_refs'],historical_validation_refs=c['validation_refs'],qualification='NOT_RUN'))
  rows.append(dict(topic=t['d3_id'],owner=t['owner'],requirement_id=t['requirement_id'],label=req['label'],research_requirement=req['research_requirement'],negative_boundary=req['negative_boundary'],claims=cands,case_ids=t['topic_case_refs'],historical_relations=t['topic_relation_refs'],status='PREPARATION_NOT_ADEQUACY_VERDICT'))
assert len(rows)==100
seen={(c['claim_id'],s['source_id']) for t in rows for c in t['claims'] for s in c['source_associations']}
assert set(checks)<=seen
out={}
for o in MODS:
 rr=[r for r in rows if r['owner']==o];cc=[c for r in rr for c in r['claims']];ss=[s for c in cc for s in c['source_associations']]
 out[o]=dict(topics=len(rr),claims=len(cc),source_associations=len(ss),missing_historical=sum('MISSING' in s['historical_location_status'] for s in ss),historical_located=sum('MISSING' not in s['historical_location_status'] for s in ss),new_limited_locator_checks=sum(s['recheck'] is not None for s in ss),topics_without_any_new_check=sum(not any(s['recheck'] for c in r['claims'] for s in c['source_associations']) for r in rr))
 write(P/(o+'-research-inventory.json'),rr)
assert sum(x['claims'] for x in out.values())==242
write(P/'summary.json',dict(status='PREPARATION_ONLY_NOT_FORMAL_MODULE_DELIVERY',ledger_manifest_sha256=sha(Q/'ledger-manifest.json'),source_inputs=sorted(inputs,key=lambda x:x['path']),modules=out,limited_source_checks=len(checks),source_access_failure=['K05-S08 PubMed returned no usable abstract','K07-S07 NASEM body find timed out; no new verified locator'],qualification='NOT_RUN'))
print(out)
