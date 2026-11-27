"""Builder-only exact synthetic probes; no learner or scientific effect inference."""
import json,pathlib,hashlib
from fractions import Fraction as F
P=pathlib.Path(__file__).resolve().parent
def q(v):
 if type(v) not in (int,str):raise ValueError('missing/type')
 return F(v)
def n(v):
 if type(v) is not int or v<0:raise ValueError('count')
 return v
def prob(v):
 r=q(v)
 if not 0<=r<=1:raise ValueError('range')
 return r
def calc(m,a):
 try:
  if m=='difference':
   x,y,matched=a
   if matched is not True: return 'HOLD'
   x,y=q(x),q(y)
   if not(0<=x<=100 and 0<=y<=100):return 'HOLD'
   return str(x-y)
  if m=='ratio':
   x,y=map(n,a)
   return str(F(x,y)) if 0<y and x<=y else 'HOLD'
  if m=='schedule':
   times,end=a; times=list(map(q,times));end=q(end)
   if not times or times[0]<0 or any(y<=x for x,y in zip(times,times[1:])) or end<times[-1]:return 'HOLD'
   return {'gaps':[str(y-x) for x,y in zip(times,times[1:])],'retention':str(end-times[-1])}
  if m=='efficiency':
   x,t,k,matched=a;x,t,k=n(x),q(t),n(k)
   return {'rate':str(x/t),'meets':x>=k} if matched is True and t>0 else 'HOLD'
  if m=='independent':
   correct,tool_ok,hint=a
   if any(type(x) is not bool for x in a) or not tool_ok:return 'HOLD'
   return 'ASSISTED' if hint else ('INDEPENDENT_EVIDENCE' if correct else 'INCORRECT')
  if m=='threshold':
   x,y,minimum,t,ind=a;x,y,minimum=n(x),n(y),n(minimum);t=prob(t)
   if not 0<minimum<=y or x>y or ind is not True:return 'HOLD'
   return 'MEETS_RULE' if F(x,y)>=t else 'BELOW_RULE'
  if m=='budget':
   costs,budget=a; costs=list(map(q,costs));budget=q(budget)
   return str(max(F(0),sum(costs)-budget)) if budget>=0 and all(x>=0 for x in costs) else 'HOLD'
  if m=='calibration':
   p,y=a;p=list(map(prob,p));y=list(map(prob,y))
   if not p or len(p)!=len(y):return 'HOLD'
   d=[x-z for x,z in zip(p,y)];return {'bias':str(sum(d)/len(d)),'mae':str(sum(map(abs,d))/len(d))}
  raise RuntimeError('unknown mode')
 except (TypeError,ValueError,ZeroDivisionError):return 'HOLD'
rows=json.loads((P/'finite-oracles.json').read_text())
results=[]
for x in rows:
 got=calc(x['mode'],x['input'])
 if got!=x['expected']:raise AssertionError((x['id'],got,x['expected']))
 results.append({'id':x['id'],'actual':got,'status':'PASS_BUILDER_FINITE_ONLY'})
(P/'oracle-results.json').write_text(json.dumps({'status':'BUILDER_ONLY','fixture_sha256':hashlib.sha256((P/'finite-oracles.json').read_bytes()).hexdigest(),'results':results},ensure_ascii=False,indent=2)+'\n')
print(len(results),'PASS_BUILDER_FINITE_ONLY')
