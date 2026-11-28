"""Finite source-bound symbolic examples, not speech recognition or general grammar parser."""
import re, unicodedata

def _evaluate(rule,x):
 if not isinstance(x,dict):return 'HOLD'
 if rule=='tone_pair':
  if x.get('unit')!='TONE_CATEGORY' or x.get('same_domain') is not True or x.get('surface_only') is True or x.get('rule_scope')!='THIRD_TONE_PAIR_ONLY':return 'HOLD'
  t=x.get('citation_tones')
  if not isinstance(t,list) or len(t)!=2 or any(type(v)is not int or v not in range(1,5) for v in t):return 'HOLD'
  return [2,3] if t==[3,3] else t
 if rule=='bu_tone':
  if x.get('form')!='不' or x.get('context')!='ORDINARY_NEGATION_BEFORE_TONED_SYLLABLE':return 'HOLD'
  t=x.get('following_tone')
  return 2 if type(t)is int and t==4 else 4 if type(t)is int and t in (1,2,3) else 'HOLD'
 if rule=='initial_spelling':
  if x.get('representation')!='PINYIN_INITIAL_FIELD' or x.get('known_initial') not in ('b','p','m','f','d','t','n','l','g','k','h','j','q','x','zh','ch','sh','r','z','c','s'):return 'HOLD'
  return 1 if x.get('query')=='INITIAL_COUNT' else 'HOLD'
 if rule=='tone_value':
  if x.get('representation')!='CHAO_RELATIVE_FIVE_POINT' or not isinstance(x.get('contour'),list) or not x['contour'] or any(type(v)is not int or not 1<=v<=5 for v in x['contour']):return 'HOLD'
  if x.get('query')=='ABSOLUTE_HZ':return 'HOLD'
  if x.get('query')!='DIRECTION' or len(x['contour'])<2:return 'HOLD'
  a=x['contour'];return 'LEVEL' if len(set(a))==1 else 'RISING' if all(i<=j for i,j in zip(a,a[1:])) else 'FALLING' if all(i>=j for i,j in zip(a,a[1:])) else 'NON_MONOTONIC'
 if rule=='glyph_identity':
  a,b=x.get('a'),x.get('b')
  if x.get('query')!='ENCODED_SCALAR_EQUALITY' or not isinstance(a,str) or not isinstance(b,str) or len(a)!=1 or len(b)!=1 or any(0xD800<=ord(v)<=0xDFFF for v in (a,b)):return 'HOLD'
  return 'SAME_CODEPOINT' if ord(a)==ord(b) else 'DISTINCT_CODEPOINT'
 if rule=='variant_context':
  if x.get('mapping_version')!='UAX38_41_EXAMPLE_CONTEXT' or x.get('source')!='脏' or x.get('direction')!='SC_TO_TC':return 'HOLD'
  return {'VISCERA':'臟','DIRTY':'髒'}.get(x.get('sense'),'HOLD')
 if rule=='stroke_source':
  if x.get('query')!='RECORDED_STROKE_COUNT' or x.get('same_glyph_standard') is not True or x.get('property')!='kTotalStrokes' or x.get('version')!='UAX38_41' or type(x.get('count'))is not int or not 1<=x['count']<=999:return 'HOLD'
  return x['count']
 if rule=='mandarin_property':
  if x.get('property')!='kMandarin' or x.get('query')!='RECORDED_READING_PROPERTY' or x.get('version')!='UAX38_41' or not isinstance(x.get('values'),list) or len(x['values']) not in (1,2):return 'HOLD'
  # Exact UAX38 property syntax on NFD; additionally reject mark-only strings.
  # Syntax acceptance is not phonotactic validation or a database lookup.
  for v in x['values']:
   if not isinstance(v,str):return 'HOLD'
   nfd=unicodedata.normalize('NFD',v)
   if not re.fullmatch(r'[a-z\u0300-\u0302\u0304\u0308\u030c]+',nfd) or not re.search(r'[a-z]',nfd):return 'HOLD'
  return x['values']
 if rule=='segmentation':
  if x.get('construction') not in ('RESULTATIVE','POTENTIAL'):return 'HOLD'
  if x.get('treebank')=='UD_CHINESE_HK' and x.get('query')=='TOKEN_BOUNDARY_POLICY':return 'SEPARATE_TOKENS'
  if x.get('treebank')=='PENN_CHINESE' and x.get('query')=='TOKEN_BOUNDARY_POLICY':return 'CONDITION_DEPENDENT'
  return 'HOLD'
 if rule=='pos_context':
  if x.get('framework')!='UD_ZH_V2' or x.get('word') not in ('能','会','可以','肯','敢','应该') or x.get('query')!='ANNOTATION_ROLE':return 'HOLD'
  if x.get('preverbal_modal') is True and x.get('direct_object') is False and x.get('aspect_after') is False:return 'AUX_CANDIDATE'
  if x.get('direct_object') is True and x.get('preverbal_modal') is False:return 'NOT_MODAL_AUX_RULE'
  return 'HOLD'
 if rule=='affix_token':
  if x.get('framework')!='UD_ZH_V2' or x.get('treebank')!='UD_CHINESE' or x.get('query')!='RECORDED_AFFIX_RELATION' or x.get('separate_token') is not True:return 'HOLD'
  return {'PREFIX':'case:pref','SUFFIX':'case:suff'}.get(x.get('kind'),'HOLD')
 if rule=='compound_annotation':
  if x.get('framework')!='UD_ZH_V2' or x.get('query')!='ANNOTATION_CANDIDATE' or x.get('verified_noun_noun') is not True:return 'HOLD'
  if x.get('possessive') is True:return 'nmod'
  if x.get('possessive') is False:return 'compound'
  return 'HOLD'
 if rule=='aspect':
  if x.get('framework')!='UD_ZH_V2' or x.get('query')!='ASPECT_ANNOTATION' or x.get('postverbal') is not True or x.get('sentence_final_only') is not False:return 'HOLD'
  return {'了':'PERFECTIVE','过':'EXPERIENTIAL','着':'DURATIVE'}.get(x.get('marker'),'HOLD')
 if rule=='ba_passive':
  if x.get('framework')!='UD_ZH_V2' or x.get('query')!='CASE_ANNOTATION' or x.get('verified_construction') is not True:return 'HOLD'
  if x.get('marker')=='把' and x.get('role')=='VALENCE_MARKER':return 'case'
  if x.get('marker')=='被' and x.get('role')=='LONG_PASSIVE_AGENT_MARKER' and x.get('agent_expressed') is True:return 'case'
  return 'HOLD'
 if rule=='de_marker':
  if x.get('framework')!='UD_ZH_V2' or x.get('query')!='PARTICLE_ANNOTATION' or x.get('marker')!='的':return 'HOLD'
  return {'GENITIVE':'case','RELATIVIZER':'mark:rel'}.get(x.get('function'),'HOLD')
 if rule=='argument_role':
  if x.get('framework')!='UD_ZH_V2' or x.get('query')!='DEPENDENCY_ROLE':return 'HOLD'
  if x.get('verified_role')=='NOMINAL_SUBJECT' and x.get('preposition') is False:return 'nsubj'
  if x.get('verified_role')=='DIRECT_CORE_OBJECT' and x.get('preposition') is False:return 'obj'
  if x.get('verified_role')=='INDIRECT_CORE_OBJECT' and x.get('preposition') is False:return 'iobj'
  if x.get('verified_role')=='PREPOSITIONAL_OBLIQUE_ARGUMENT' and x.get('preposition') is True:return 'obl:arg'
  return 'HOLD'
 return 'HOLD'

def evaluate(rule,x):
 # Malformed field values are unknown, not uncaught classification errors.
 try:return _evaluate(rule,x)
 except (TypeError,ValueError,KeyError):return 'HOLD'
