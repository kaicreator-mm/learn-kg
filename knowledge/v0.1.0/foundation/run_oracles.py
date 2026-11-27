#!/usr/bin/env python3
"""Finite author-frozen synthetic expectations, not independent scientific qualification."""
import json,math
from fractions import Fraction as F
from statistics import NormalDist
from pathlib import Path
P=Path(__file__).resolve().parent
def calc(m,x):
 try:
  if m=='rw2':
   l,a,b,ra,rb=(F(x[k]) for k in ('lambda','a','b','rate_a','rate_b'))
   if not all(0<=q<=1 for q in (l,a,b,ra,rb)):return 'HOLD'
   return [str(ra*(l-a-b)),str(rb*(l-a-b))]
  if m=='sdt':
   h=F(x['hit'],x['signal']);f=F(x['fa'],x['noise'])
   if not 0<h<1 or not 0<f<1:return 'HOLD'
   zh,zf=NormalDist().inv_cdf(float(h)),NormalDist().inv_cdf(float(f))
   return [zh-zf,-(zh+zf)/2]
  if m=='switch':return [x['mixed_switch']-x['mixed_repeat'],x['mixed_repeat']-x['single']]
  if m=='savings':
   if x['same_standard'] is not True or x['initial']<=0 or x['relearn']<0:return 'HOLD'
   return str(F(x['initial']-x['relearn'],x['initial']))
  if m=='paths':
   if not x or any(not g or any(v not in ('TRUE','FALSE','UNKNOWN') for v in g) for g in x):return 'HOLD'
   results=['FALSE' if 'FALSE' in g else 'UNKNOWN' if 'UNKNOWN' in g else 'TRUE' for g in x]
   return 'TRUE' if 'TRUE' in results else 'UNKNOWN' if 'UNKNOWN' in results else 'FALSE'
  if m=='ratio':
   a,b=F(x['hard']),F(x['simple'])
   return str(a/b) if x['assumptions'] is True and 0<=a<=b<=1 and b>0 else 'HOLD'
  if m=='motor':
   if x['sign_defined'] is not True:return 'HOLD'
   return str(F(x['x'])*F(x['r'])+F(x['k'])*F(x['e']))
  if m=='fitts_id':
   if x['unit_match'] is not True or x['A']<0 or x['W']<=0:return 'HOLD'
   return math.log2(1+x['A']/x['W'])
 except (KeyError,ValueError,ZeroDivisionError,TypeError):return 'HOLD'
 raise ValueError(m)
def equal(a,b):
 if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
 if type(a) in (int,float) and type(b) in (int,float):return math.isclose(a,b,abs_tol=1e-8,rel_tol=0)
 return type(a)==type(b) and a==b
rows=[]
for c in json.loads((P/'finite-oracles.json').read_text()):
 a=calc(c['mode'],c['input']);assert equal(a,c['expected']),(c['id'],a,c['expected'])
 rows.append({'id':c['id'],'actual':a,'status':'PASS_BUILDER_FINITE_ONLY'})
(P/'oracle-results.json').write_text(json.dumps({'status':'BUILDER_SYNTHETIC_ONLY','results':rows,'independent_qualification':'NOT_RUN','limits':'Fixed author expectations; independent reviewer must check derivation and negative boundaries. No actual learner, scientific effect, parameter calibration or formal CQ/LC.'},ensure_ascii=False,indent=2)+'\n')
print('FINITE_ORACLES',len(rows))
