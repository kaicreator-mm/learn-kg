"""Replay all P cases on the exact integrated candidate-3 SQL snapshot; author tests only."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
DOC=Path(__file__).resolve().parent
P=ROOT/'docs/implementation/process-cumulative'
B=ROOT/'knowledge/v0.1.0'
OLD=B/'learning-process-cumulative-r2'
PKG=B/'learning-process-cumulative-r4'
V='0.1.0-process-candidate-4'
sys.path[:0]=[str(P),str(ROOT)]
import build as pb
from policy_entry import policy_eval
import inspect
assert inspect.getsource(policy_eval)==inspect.getsource(pb.policy_eval).replace("expected_version='0.1.0-process-candidate-2'","expected_version=None").replace("if expected_version not in ('0.1.0-process-candidate-2','0.1.0-process-candidate-3'):return 'HOLD'","if expected_version!='0.1.0-process-candidate-4':return 'HOLD'")
from inherited import replay
from tools.knowledge_import.importer import Importer,ManifestPin
from tools.knowledge_import.v00_prototype import load_record

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(root):
    m=load(root/'learning-process.manifest.json')
    result={}
    for f in m['files']:
        p=root/f['path'];assert sha(p)==f['sha256']
        for line in p.read_text(encoding='utf-8').splitlines():
            r=json.loads(line);assert r['stable_id'] not in result;result[r['stable_id']]=r
    return result
def main():
    target=rows(PKG);source=rows(OLD)
    def local(id):
        r=target[id];return pb.ref(r['owner'],r['kind'],id,V)
    catalog={}
    for p in B.glob('*/*manifest.json'):
        m=load(p)
        if not {'package_id','version'}<=m.keys():continue
        k=m['package_id'],m['version'];pin=ManifestPin(p.relative_to(ROOT).as_posix(),sha(p))
        if k in catalog:assert catalog[k].sha256==pin.sha256
        catalog[k]=pin
    ext=B/'foundation-r3'/'relation-types.json'
    im=Importer(mode='research',catalog=catalog,extension=ManifestPin(ext.relative_to(ROOT).as_posix(),sha(ext)))
    try:
        im.run(('learning-process',V))
        inherited={k:r for k,r in source.items() if r['owner'] in ('P01','P02','P03')}
        h=replay(im,local,inherited,pb.remap,V,ROOT,load_record,pb.check,pb.dig)
        cases=load(P/'fixtures.json')
        out=[]
        for f in cases:
            c=load_record(im,local(f['case_id']))
            x=json.loads(c['input_spec']);assert x==f['input']
            t=c['target_refs'][0];assert t['version']==V
            a=load_record(im,t)
            if f.get('evaluation_kind')=='P09_POLICY_GATE':
                y=pb.p09_policy_eval(im,t,x)
            elif x.get('scenario')=='CONCRETE_FINITE':
                y=pb.evaluate(im,a,x,f['owner'],load_record)
            elif f['owner']=='P07':
                y=policy_eval(im,t,x,expected_version=V)
            else:
                y=pb.flow_eval(im,a,x,f['owner'])
            expected=json.loads(c['expected_spec']) if isinstance(f['expected'],dict) else c['expected_spec']
            assert y==expected==f['expected'],(f['case_id'],y,expected)
            val=load_record(im,local(f['case_id']+'.VAL'))
            assert val['input_digest']==pb.dig(x) and val['result_digest']==pb.dig(y)
            out.append(dict(owner=f['owner'],case_id=f['case_id'],actual=y))
        # Direct adversarial route checks at the target tuple: no caller policy object,
        # no P09 ref at generic P07 entry, and no candidate-2 tuple in this invocation.
        p09=local('P09.POLICY');p07=local('P07.POLICY')
        forged={'rules':[{'condition_ref':None,'action':'SUGGEST','reason':'FORGED','priority':1}]}
        x={'exit':False,'declined':False,'paused':False,'selected':'FORGED'}
        probes=[(forged,'HOLD'),(p09,'HOLD'),({**p07,'version':'0.1.0-process-candidate-2'},'HOLD'),({**p07,'rules':forged['rules']},'HOLD')]
        for value,expected in probes:assert policy_eval(im,value,x,expected_version=V)==expected
        assert policy_eval(im,p07,{'exit':True},expected_version=V)=='STOP'
        assert policy_eval(im,p07,{'exit':True})=='HOLD'
        assert policy_eval(im,p07,{'exit':True},expected_version='0.1.0-process-candidate-3')=='HOLD'
        assert len(out)==360 and len(h['results'])==143 and len(source)==1401
        assert all(all(row[2]=='' for row in c.execute('PRAGMA database_list').fetchall()) for c in im.connections.values())
        report={'status':'AUTHOR_SQL_REBIND_REGRESSION_ONLY','package_version':V,'source_manifest_sha256':sha(OLD/'learning-process.manifest.json'),'target_manifest_sha256':sha(PKG/'learning-process.manifest.json'),'migrated_records':len(source),'current_cases':len(out),'inherited_cases':len(h['results']),'total_cases':len(out)+len(h['results']),'target_tuple_probes':7,'current_results':out,'inherited_results':h['results'],'qualification':'NOT_GRANTED','persistent_sqlite':False}
        pb.write(DOC/'p-rebind-regression.json',report)
        print('P_REBIND',len(out),len(h['results']),len(source),report['target_manifest_sha256'])
    finally:im.close()
if __name__=='__main__':main()
