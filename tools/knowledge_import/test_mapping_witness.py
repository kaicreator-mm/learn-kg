"""DB02 schema/SQLite field mapping witness, synthetic only; no professional claims."""
import collections,copy,json,pathlib,tempfile,unittest
from tools.knowledge_import.importer import Importer,Reject,ROOT
from tools.knowledge_import.test_importer import Fixture,ref

def packages(f, mutate=None):
    def record(o,k,i=None,**fields): return f.base(o,k,i or k)|fields
    def cr(k,i=None):return ref('learning-core','K09',i or k,k)
    def hr(k,i=None):return ref('chinese','H01',i or k,k)
    def pr(k,i=None):return ref('learning-process','P01',i or k,k)
    sr=ref('evidence','EVIDENCE','SRC','Source')
    def claim(o,r):
        return record(o,'Claim',topic_id='Topic',requirement_id='Requirement',claim_type='SYNTHETIC_MAPPING_ONLY',statement='合成字段映射，不是专业知识',source_status='SYNTHETIC',locator_refs=[],case_refs=[],validation_refs=[],supersedes_refs=[],refinement_of=None)
    def basics(o,r):
        return [record(o,'Topic',label='合成主题',depth=1,parent_ref=None),record(o,'Requirement',topic_ref=r('Topic'),scope='mapping only',source_leads=[],coverage_status='CANDIDATE_NOT_QUALIFIED'),claim(o,r)]
    c=basics('K09',cr)
    def core(k,**fields):c.append(record('K09',k,**fields))
    claims=[cr('Claim')]
    core('Locator',source_ref=sr,location='synthetic',attribution='RECORDED_NOT_REVERIFIED',verification='NOT_RUN')
    c[-2]['locator_refs']=[cr('Locator')]
    core('Case',target_refs=claims,view='COMPOSITION',input_spec='synthetic input',expected_spec='synthetic expected',oracle_ref=cr('Validation'),actual_status='NOT_RUN')
    core('Validation',target_refs=claims,case_refs=[cr('Case')],method='synthetic only',oracle_identity=None,input_digest=None,result_digest=None,run_status='NOT_RUN')
    c[2]['case_refs']=[cr('Case')];c[2]['validation_refs']=[cr('Validation')]
    core('Element',topic_id='Topic',element_type='synthetic',label='构念',definition='synthetic',claim_refs=claims)
    core('KnowledgeType',claim_refs=claims,label='knowledge',definition='synthetic')
    core('SkillType',claim_refs=claims,label='skill',performance_boundary='synthetic')
    core('Competency',claim_refs=claims,dimensions=['synthetic dimension'],evidence_refs=[cr('ObservationSpec')])
    core('Goal',claim_refs=claims,construct_ref=cr('Competency'),success_evidence_refs=[cr('ObservationSpec')],scope='synthetic target')
    core('ObservationSpec',claim_refs=claims,construct_ref=cr('Competency'),method='synthetic observation',unit='score',independence_requirement='no hints',missing='UNKNOWN_NOT_ZERO')
    core('LearningObject',claim_refs=claims,target_refs=[cr('Element')],component_refs=[],granularity='one synthetic object')
    core('TaskSpec',claim_refs=claims,construct_ref=cr('Competency'),object_refs=[cr('LearningObject')],prompt='synthetic prompt',scoring_spec='synthetic criterion',observation_refs=[cr('ObservationSpec')],independence_requirement='no hints')
    core('ModelSpec',claim_refs=claims,parameters=[{'name':'x','unit':'score','meaning':'synthetic parameter','lower':0,'upper':None}],formulas=[{'name':'f','expr':{'op':'add','args':[{'variable':'x'},{'constant':0.5}]}}],numeric_domain='BINARY64',missing_policy='HOLD',applicability=['synthetic only'])
    core('ConditionSpec',claim_refs=claims,clauses=[{'field':'matched','op':'EQ','value':True},{'field':'score','op':'GE','value':0.5}],combination='ALL',unknown='HOLD')
    core('Relation',relation_type='example_of',from_ref=cr('Case'),to_ref=cr('Claim'),claim_refs=claims,condition_refs=[cr('ConditionSpec')],direction='DIRECTED',automatic_transitive=False,automatic_inverse=False)
    h=basics('H01',hr)
    def chinese(k,**fields):h.append(record('H01',k,**fields))
    hc=[hr('Claim')]
    chinese('HanCharacter',character='学',codepoint='U+5B66',script='synthetic fixture',claim_refs=hc)
    chinese('Reading',notation='xue',system='synthetic notation',tone=None,reading_scope='fixture',claim_refs=hc)
    chinese('Lexeme',lemma='学',form_refs=[hr('HanCharacter')],reading_refs=[hr('Reading')],claim_refs=hc)
    chinese('Sense',lexeme_ref=hr('Lexeme'),gloss='synthetic sense',part_of_speech='fixture',domain='fixture',claim_refs=hc)
    chinese('Construction',pattern='synthetic slot',slot_constraints=['fixture only'],meaning='synthetic',claim_refs=hc,condition_refs=[cr('ConditionSpec')])
    chinese('Standard',edition='SYNTHETIC-NOT-HSK',standard_name='fixture only',source_refs=[sr],effective_date=None)
    chinese('StandardBand',standard_ref=hr('Standard'),raw_band='fixture band',band_scope='synthetic only')
    chinese('SourceMembership',standard_ref=hr('Standard'),band_ref=hr('StandardBand'),source_ref=sr,section='fixture',ordinal=1,printed_page=None,raw_fields=[{'name':'text','value':'学'},{'name':'blank','value':None}],mapping_status='HOLD',semantic_refs=[hr('Lexeme')])
    p=basics('P01',pr)
    def process(k,i=None,**fields):p.append(record('P01',k,i,**fields))
    pc=[pr('Claim'),cr('Claim')]
    process('Role',claim_refs=pc,label='fixture role',capability_requirements=['fixture'],permission_requirements=['affirmative choice'])
    process('Modality',claim_refs=pc,label='fixture modality',capability_requirements=['fixture'],not_equivalent_to=[])
    process('Resource',claim_refs=pc,modality_refs=[pr('Modality')],rights='HOLD',accessibility=['fixture'],resource_identity='synthetic resource')
    process('Environment',claim_refs=pc,constraints=['fixture constraint'],capabilities=['fixture capability'])
    for aid in ('Activity','Comparator'):
        process('Activity',aid,claim_refs=pc,goal_refs=[cr('Goal')],object_refs=[cr('LearningObject')],resource_refs=[pr('Resource')],role_refs=[pr('Role')],observation_refs=[cr('ObservationSpec')],budget=2,stop_condition='fixture stop')
    process('Interaction',claim_refs=pc,activity_ref=pr('Activity'),role_refs=[pr('Role')],input_contract='fixture input',output_contract='fixture output',observation_refs=[cr('ObservationSpec')],assistance_policy='no hints')
    process('Mode',claim_refs=pc,goal_refs=[cr('Goal')],activity_refs=[pr('Activity')],role_refs=[pr('Role')],selection_condition_refs=[cr('ConditionSpec')],learner_choice=True,switch_condition='fixture switch')
    process('PolicySpec',claim_refs=pc,policy_type='PRACTICE',rules=[{'condition_ref':cr('ConditionSpec'),'action':'SUGGEST','priority':1,'reason':'fixture'}],unknown_action='STOP',effect='ADVICE_ONLY')
    process('FlowSpec',claim_refs=pc,entry='start',steps=[{'id':'start','activity_ref':pr('Activity'),'max_attempts':1,'checkpoint':True}],transitions=[{'from_step':'start','to_step':'done','event':'complete','condition_ref':cr('ConditionSpec'),'priority':1,'consumes_budget':True},{'from_step':'start','to_step':'stop','event':'stop','condition_ref':None,'priority':0,'consumes_budget':False}],terminals=[{'id':'done','outcome':'COMPLETE'},{'id':'stop','outcome':'STOP'},{'id':'unknown','outcome':'HOLD'}],max_events=2,unknown_terminal='unknown',stop_terminal='stop',parallel_joins=[],effect='TEMPLATE_ONLY')
    process('StateDimension',claim_refs=pc,construct_ref=cr('Competency'),observation_refs=[cr('ObservationSpec')],estimator_ref=cr('ModelSpec'),uncertainty='fixture only',effect='DEFINITION_ONLY')
    process('EvaluationProtocol',claim_refs=pc,goal_ref=cr('Goal'),intervention_ref=pr('Activity'),comparator_ref=pr('Activity','Comparator'),measurement_refs=[cr('ObservationSpec')],estimand='fixture contrast',population_scope='synthetic only',followup='fixture',uncertainty='not estimated',approval_required=True,effect='NO_DIRECT_KNOWLEDGE_WRITE')
    process('CompositionSpec',claim_refs=pc,view_id='fixture-view',input_refs=[hr('Lexeme'),cr('Goal')],output_refs=[pr('PolicySpec')],condition_refs=[cr('ConditionSpec')],alternative_refs=[],failure_policy='STOP',evidence_refs=[cr('Case')],effect='CANDIDATE_DECISION_ONLY')
    e=[f.source_record()]
    if mutate:mutate(e,c,h,p)
    ev=f.pkg('evidence','EVIDENCE',e)
    ck=f.pkg('learning-core','K09',c,deps=(ev,))
    hk=f.pkg('chinese','H01',h,deps=(ev,ck))
    pk=f.pkg('learning-process','P01',p,deps=(ev,ck,hk))
    return pk,(e,c,h,p)

class MappingWitness(unittest.TestCase):
    def with_fixture(self,fn):
        with tempfile.TemporaryDirectory() as d:return fn(Fixture(d))
    def test_all_38_kinds_actual_roundtrip(self):
        def run(f):
            root,groups=packages(f);im=Importer(f.root,mode='research',catalog=f.catalog)
            try:
                r=im.run(root);expected=collections.Counter(x['kind'] for g in groups for x in g)
                got=collections.Counter()
                for p in r['packages']:got.update(p['counts'])
                self.assertEqual(got,expected)
                self.assertEqual(set(got),set(im.mapping['record_tables'])-{'ref'})
                self.assertEqual(len(got),38)
                self.assertEqual(len(im.connections),4)
                for key,c in im.connections.items():
                    self.assertTrue(all(path=='' for _,_,path in c.execute('PRAGMA database_list')))
                    self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])
                    self.assertEqual(c.execute('PRAGMA integrity_check').fetchone(),('ok',))
                    self.assertEqual(c.execute('PRAGMA query_only').fetchone(),(1,))
                self.assertFalse(r['persistent_sqlite'])
            finally:im.close()
        self.with_fixture(run)
    def test_each_kind_missing_required_semantic_field(self):
        fields=json.loads((ROOT/'docs/implementation/db01/canonical.schema.json').read_text())['$defs']
        kinds=set(json.loads((ROOT/'docs/implementation/db01/mapping-contract.json').read_text())['record_tables'])-{'ref'}
        for kind in sorted(kinds):
            with self.subTest(kind=kind):
                def run(f):
                    def mut(*groups):
                        x=next(x for g in groups for x in g if x['kind']==kind)
                        field=next(k for k in fields[kind]['required'] if k not in {'kind','stable_id','owner','status','conditions','negative_boundary','provenance'})
                        del x[field]
                    root,_=packages(f,mut)
                    with self.assertRaisesRegex(Reject,'SCHEMA'):f.run(root)
                self.with_fixture(run)
    def test_cross_domain_version_and_effect_rejections(self):
        def wrong_version(e,c,h,p):
            next(x for x in p if x['kind']=='CompositionSpec')['input_refs'][0]['version']='other'
        def wrong_owner(e,c,h,p):
            next(x for x in h if x['kind']=='Lexeme')['form_refs'][0]['owner']='H02'
        def wrong_effect(e,c,h,p):
            next(x for x in p if x['kind']=='EvaluationProtocol')['approval_required']=False
        for mut,code in [(wrong_version,'UNDECLARED_DIRECT_DEPENDENCY'),(wrong_owner,'REF_IDENTITY'),(wrong_effect,'SCHEMA')]:
            with self.subTest(mut=mut.__name__):
                def run(f):
                    root,_=packages(f,mut)
                    with self.assertRaisesRegex(Reject,code):f.run(root)
                self.with_fixture(run)
if __name__=='__main__':unittest.main()
