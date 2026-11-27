"""Finite project-policy and synthetic observation cases, not legal/clinical decisions."""
import json,pathlib,hashlib
from fractions import Fraction as F
P=pathlib.Path(__file__).resolve().parent
def need(x):
 if not x:raise ValueError('domain')
def n(v):need(type(v) in (str,int,float));return F(str(v))
def nat(v):need(type(v) is int and v>=0);return v
def text(v):need(isinstance(v,str) and bool(v.strip()));return v
def gate(m,x):
 try:
  if m=='event':
   a,b=text(x['old_id']),text(x['new_id']);c,d=text(x['old_hash']),text(x['new_hash'])
   need(x.get('authorized') is True)
   if a!=b:return 'NEW_EVENT_CANDIDATE'
   return 'DUPLICATE_NO_UPDATE' if c==d else 'CONFLICT_HOLD'
  if m=='available':
   a,b,c=[n(x[k]) for k in ('event_time','available_at','prediction_time')]
   need(x.get('same_clock') is True and a<=b)
   return 'AVAILABLE' if a<=c and b<=c else 'EXCLUDE_FUTURE_OR_UNAVAILABLE'
  if m=='metric':
   a,b,c=[nat(x[k]) for k in ('correct','incorrect','missing')];need(x.get('same_target') is True)
   p=x['denominator'];den=a+b if p=='VALID_RESPONSE' else a+b+c if p=='ALL_ADMINISTERED' else 0
   need(den>0);return str(F(a,den))
  if m=='adaptation':
   if x.get('confirmed_need') is not True:return 'CLARIFY'
   if x.get('authorized') is False:return 'REFUSE'
   need(x.get('authorized') is True)
   c=x.get('construct_preserved');v=x.get('actual_access_verified')
   if c is False:return 'SEPARATE_CONSTRUCT'
   if c is True and v is True:return 'SUGGEST_REVERSIBLE_SUPPORT_ONLY'
   return 'HOLD'
  if m=='access':
   # A project authorization rule, not statutory interpretation.
   if x.get('revoked') is True:return 'REFUSE'
   keys=('identity_verified','role_permitted','purpose_permitted','scope_permitted','within_term','revoked')
   expected=(True,True,True,True,True,False)
   if any(type(x.get(k)) is bool and x[k]!=e for k,e in zip(keys,expected)):return 'REFUSE'
   if not all(type(x.get(k)) is bool and x[k]==e for k,e in zip(keys,expected)):return 'HOLD'
   return 'AUTHORIZED_CANDIDATE_ONLY'
  if m=='purpose':
   if x.get('withdrawn') is True:return 'REFUSE'
   need(x.get('withdrawn') is False)
   a,b=text(x['authorized_purpose']),text(x['requested_purpose'])
   if a!=b:
    if x.get('new_purpose_authorized') is False:return 'REFUSE'
    if x.get('new_purpose_authorized') is not True:return 'HOLD'
   elif x.get('original_authorization_valid') is False:return 'REFUSE'
   elif x.get('original_authorization_valid') is not True:return 'HOLD'
   if x.get('applicable_requirements_checked') is not True:return 'HOLD'
   return 'AUTHORIZED_CANDIDATE_ONLY'
  if m=='publication':
   if x.get('public_release_allowed') is False:return 'REFUSE'
   return 'REVIEW_CANDIDATE_ONLY' if all(x.get(k) is True for k in ('source_identity_verified','public_release_allowed','scope_checked','reviewer_approved')) else 'HOLD'
  if m=='decision':
   if x.get('withdrawn') is True:return 'STOP'
   need(x.get('withdrawn') is False and type(x.get('high_risk')) is bool)
   if x['high_risk']:return 'DEFER_TO_AUTHORIZED_HUMAN'
   if x.get('authorized') is False:return 'REFUSE'
   return 'SUGGEST_ONLY' if x.get('authorized') is True and x.get('evidence_matches') is True else 'HOLD'
  if m=='roundtrip':
   a,b=x['before'],x['after'];need(isinstance(a,dict) and isinstance(b,dict))
   fields=x['required_fields'];need(isinstance(fields,list) and fields and all(isinstance(k,str) and k for k in fields) and len(set(fields))==len(fields))
   if any(k not in a or k not in b for k in fields):return 'LOSS_HOLD'
   if any(type(a[k])!=type(b[k]) or a[k]!=b[k] for k in fields):return 'LOSS_HOLD'
   return 'MATCH_SCOPED_FIELDS_ONLY'
 except (ValueError,TypeError,KeyError,ZeroDivisionError,OverflowError,IndexError):return 'HOLD'
 raise ValueError(m)
def main():
 f=P/'finite-fixtures.json';rows=json.loads(f.read_text());out=[]
 for x in rows:
  v=gate(x['mode'],x['input']);assert v==x['expected'],(x['id'],v,x['expected'])
  out.append({'id':x['id'],'actual':v,'expected':x['expected'],'status':'PASS_BUILDER_FINITE_ONLY'})
 (P/'finite-results.json').write_text(json.dumps(dict(fixture_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),results=out,limits='Finite project rules and arithmetic only; no independent qualification or legal, clinical, security implementation or real learner verdict.'),ensure_ascii=False,indent=2)+'\n')
 print(len(out),'PASS_BUILDER_FINITE_ONLY')
if __name__=='__main__':main()
