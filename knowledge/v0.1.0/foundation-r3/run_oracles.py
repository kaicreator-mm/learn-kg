#!/usr/bin/env python3
"""Finite author tests; no independent professional qualification."""
import json, math
from fractions import Fraction as F
from statistics import NormalDist
from pathlib import Path
P=Path(__file__).resolve().parent
def q(x):
    if type(x) not in (int,float,str): raise ValueError('numeric type')
    if type(x)==float and not math.isfinite(x): raise ValueError('finite')
    return F(x)
def count(x):
    if type(x)!=int or x<0: raise ValueError('count')
    return x
def calc(m,x):
    try:
        if m=='rw2':
            l,a,b,ra,rb=(q(x[k]) for k in ('lambda','a','b','rate_a','rate_b'))
            if not all(0<=v<=1 for v in (l,a,b,ra,rb)):return 'HOLD'
            return [str(ra*(l-a-b)),str(rb*(l-a-b))]
        if m=='sdt':
            h,n,f,z=(count(x[k]) for k in ('hit','signal','fa','noise'))
            if not 0<h<n or not 0<f<z:return 'HOLD'
            zh,zf=NormalDist().inv_cdf(h/n),NormalDist().inv_cdf(f/z)
            return [zh-zf,-(zh+zf)/2]
        if m=='switch':
            a,b,c=(q(x[k]) for k in ('single','mixed_repeat','mixed_switch'))
            if min(a,b,c)<0:return 'HOLD'
            return [float(c-b),float(b-a)]
        if m=='savings':
            a,b=(count(x[k]) for k in ('initial','relearn'))
            if x['same_standard'] is not True or a==0:return 'HOLD'
            return str(F(a-b,a))
        if m=='paths':
            if not isinstance(x,list) or not x or any(not isinstance(g,list) or not g or any(v not in ('TRUE','FALSE','UNKNOWN') for v in g) for g in x):return 'HOLD'
            r=['FALSE' if 'FALSE' in g else 'UNKNOWN' if 'UNKNOWN' in g else 'TRUE' for g in x]
            return 'TRUE' if 'TRUE' in r else 'UNKNOWN' if 'UNKNOWN' in r else 'FALSE'
        if m=='ratio':
            a,b=q(x['hard']),q(x['simple'])
            return str(a/b) if x['assumptions'] is True and 0<=a<=b<=1 and b>0 else 'HOLD'
        if m=='motor':
            a,r,k,e=(q(x[n]) for n in ('x','r','k','e'))
            if x['sign_defined'] is not True or not 0<=r<=1 or not 0<=k<=1:return 'HOLD'
            return str(a*r+k*e)
        if m=='fitts_id':
            a,w=q(x['A']),q(x['W'])
            if x['unit_match'] is not True or a<0 or w<=0:return 'HOLD'
            return math.log2(1+float(a/w))
        if m=='representation':
            p,r=x
            if any(type(a)!=int or a not in (0,1) for a in x):return 'HOLD'
            return [bool(p and r),8*p+8*r>=7]
        if m=='feature':
            if x.get('aligned_rule_declared') is not True:return 'HOLD'
            raw=x.get('cells')
            if not isinstance(raw,list) or any(not isinstance(a,list) or len(a)!=2 or any(type(v)!=int for v in a) for a in raw):return 'HOLD'
            cells={tuple(a) for a in raw}
            if len(cells)!=len(raw):return 'HOLD'
            t={(0,0),(1,0),(2,0),(1,1),(1,2)}
            feature=any({(i,j),(i+1,j),(i+2,j),(i+1,j+1),(i+1,j+2)}==cells for i,j in cells)
            return [feature,cells==t]
        if m=='wm':
            k=count(x['k']);n=count(x['n'])
            if not k or not n:return 'HOLD'
            return [str(min(F(1),F(k,n))),'1',str(F(k,n))]
        if m=='dual':
            if x.get('matched') is not True:return 'HOLD'
            a,b,c,d=(q(x[k]) for k in ('vv','vs','sv','ss'))
            if not all(0<=v<=1 for v in (a,b,c,d)):return 'HOLD'
            return [str(b-a),str(c-d)]
        if m=='category':
            a,b=[[q(v) for v in x[k]] for k in ('a','b')];v=q(x['x'])
            if not a or not b:return 'HOLD'
            def choose(a,b):return 'A' if a>b else 'B' if b>a else 'UNKNOWN'
            return [choose(-abs(v-sum(a)/len(a)),-abs(v-sum(b)/len(b))),choose(sum(1/(1+abs(v-e)) for e in a),sum(1/(1+abs(v-e)) for e in b)),'A' if v>=7 else 'B']
        if m=='skos':
            direct={tuple(v) for v in x['broader']};related={tuple(v) for v in x['related']}; related|={(b,a) for a,b in related}
            closure=set(direct)
            while True:
                added={(a,d) for a,b in closure for c,d in closure if b==c}-closure
                if not added:break
                closure|=added
            a,b=x['query']
            return [(a,b) in direct,(a,b) in closure,(b,a) in direct,(a,b) in related or (b,a) in related,bool(related&closure)]
        if m=='constraint':
            app=x.get('applicable')
            if app is False:return 'NOT_APPLICABLE'
            target=x.get('type')
            # Target membership is a selector, not a constrained field.
            # False conjunction dominates unknown; no field evaluation outside scope.
            if isinstance(target,str) and target and target!='Assessment':return 'NOT_APPLICABLE'
            if app is not True or target!='Assessment':return 'UNKNOWN'
            missing=False
            if 'score' not in x:missing=True
            else:
                try:v=q(x['score'])
                except (ValueError,TypeError,ZeroDivisionError):return 'VIOLATED'
                if type(x['score']) not in (int,float) or not 0<=v<=1:return 'VIOLATED'
            for k in ('independent','hinted'):
                if k not in x:missing=True
                elif type(x[k])!=bool:return 'VIOLATED'
            if x.get('independent') is True and x.get('hinted') is True:return 'VIOLATED'
            return 'UNKNOWN' if missing else 'SATISFIED'
        if m=='metrics':
            a=[q(v) for v in x['errors']]
            if not a:return 'HOLD'
            return [str(sum(a)/len(a)),str(sum(abs(v) for v in a)/len(a)),str(max(a)-min(a))]
    except (KeyError,ValueError,ZeroDivisionError,TypeError,OverflowError):return 'HOLD'
    raise ValueError(m)
def equal(a,b):
    if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    if type(a) in (int,float) and type(b) in (int,float):return math.isclose(a,b,abs_tol=1e-8,rel_tol=0)
    return type(a)==type(b) and a==b
def main():
    old=json.loads((P.parent/'foundation/finite-oracles.json').read_text())
    new=json.loads((P/'new-oracles.json').read_text())
    rows=[]
    for c in old+new:
        a=calc(c['mode'],c['input']);assert equal(a,c['expected']),(c['id'],a,c['expected'])
        rows.append({'id':c['id'],'actual':a,'status':'PASS_BUILDER_FINITE_ONLY'})
    out={'status':'BUILDER_SYNTHETIC_ONLY','prior_regression':len(old),'new_cases':len(new),'results':rows,'independent_qualification':'NOT_RUN'}
    (P/'oracle-results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print('FINITE_ORACLES',len(rows))
if __name__=='__main__':main()
