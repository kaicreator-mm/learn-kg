#!/usr/bin/env python3
"""Import connector-extracted HSK syllabus text into an isolated RDF staging store."""
import argparse, collections, hashlib, json, re, tempfile, shutil
from pathlib import Path
from pyoxigraph import Store, NamedNode, Literal, Quad
N="urn:learn-kg:"
NS=N+"schema:"
GRAPH=N+"graph:staging:hsk:2025-11"
TAX=N+"graph:staging:taxonomy:r1"
RDF="http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
SEP=re.compile(r"-{20,}\s+(任务|话题|词汇|汉字|语法)大纲\s+-{20,}")
PAGE=re.compile(r"(?<!\d)(\d{1,3})\s+汉考国际\s+汉考国际\s+汉考国际\s+际\s+汉考国际\s+汉考国际\s+汉考国际\s+汉考国际")
LEVEL=r"[1-6](?:（(?:[1-6]|7-9)）)*|7-9"
WORD=re.compile(r"(?<!\S)(\d{1,5})\s+("+LEVEL+r")\s+")
CHHEAD=re.compile(r"HSK（([^）]+)）(?:~（([^）]+)）)?(认读字|书写字)")
CHAR=re.compile(r"(?<!\d)(\d{1,4})\.\s*([\u3400-\u9fff\U00020000-\U000323af])(?=\s|$)")
BAND={"一":"1","二":"2","三":"3","四":"4","五":"5","六":"6","七—九":"7-9"}
def band(s):
    return BAND[s.removesuffix("级")]
def digest(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
def clean(s):
    return " ".join(s.split())
def sections(s):
    hits=list(SEP.finditer(s))
    result={}
    for i,m in enumerate(hits):
        name=m.group(1)
        if name in result: raise ValueError("duplicate section "+name)
        seg=s[m.end():hits[i+1].start() if i+1<len(hits) else len(s)]
        p=0; pages=[]
        for n in PAGE.finditer(seg):
            pages.append((int(n.group(1)),seg[p:n.start()].strip()))
            p=n.end()
        if seg[p:].strip(): raise ValueError("unmapped trailing text "+name)
        if not pages: raise ValueError("no pages "+name)
        if [x[0] for x in pages]!=list(range(pages[0][0],pages[-1][0]+1)):
            raise ValueError("page sequence "+name)
        result[name]=pages
    return result
def words(pages):
    rows=[]
    for page,body in pages:
        body=clean(body)
        header="序号 等级 词语 拼音 词性"
        if not body: continue
        if not body.startswith(header): raise ValueError(f"vocab header {page}: {body[:50]}")
        body=body[len(header):].strip()
        hits=list(WORD.finditer(body))
        if not hits or hits[0].start()!=0: raise ValueError(f"vocab rows {page}")
        for i,m in enumerate(hits):
            payload=clean(body[m.end():hits[i+1].start() if i+1<len(hits) else len(body)])
            if len(payload.split(" ",1))!=2: raise ValueError(f"vocab payload {page}")
            term,reading_pos=payload.split(" ",1)
            if not re.search(r"[\u3400-\u9fff]",term): raise ValueError(f"vocab term {page}")
            rows.append((int(m.group(1)),m.group(2),term,reading_pos,page))
    if [x[0] for x in rows]!=list(range(1,11001)): raise ValueError("vocab serial gap/duplicate")
    return rows
def chars(pages):
    rows=[]; current=None; counts=collections.Counter()
    for page,body in pages:
        body=clean(body)
        if not body: continue
        head=CHHEAD.match(body)
        if head:
            current=(head.group(3),band(head.group(1))+("-"+band(head.group(2)) if head.group(2) else ""))
            if current in counts: raise ValueError("duplicate char section")
            body=body[head.end():].strip()
        if current is None: raise ValueError("char context")
        p=0
        for m in CHAR.finditer(body):
            if body[p:m.start()].strip(): raise ValueError(f"char unparsed p{page}: {body[p:m.start()][:60]}")
            counts[current]+=1
            if int(m.group(1))!=counts[current]: raise ValueError(f"char serial p{page}")
            rows.append((*current,int(m.group(1)),m.group(2),page))
            p=m.end()
        if body[p:].strip(): raise ValueError(f"char trailing p{page}: {body[p:][:80]}")
    if len(counts)!=13: raise ValueError("char section count")
    return rows
def blocks(secs):
    out=[]
    for section in ("任务","话题","语法"):
        active=None
        for page,body in secs[section]:
            if not body.strip(): continue
            head=re.match(r"HSK（([^）]+)）"+section,body)
            if head: active=band(head.group(1))
            if active is None: raise ValueError("block level context")
            out.append((section,active,page,body))
    return out
def abilities(text):
    hits=list(re.finditer(r"HSK（([一二三四五六七八九])级）",text))
    if len(hits)!=9: raise ValueError("ability count")
    return [(i+1,clean(text[m.end():hits[i+1].start() if i+1<len(hits) else len(text)])) for i,m in enumerate(hits)]
def query_count(store,pattern,graph=GRAPH):
    return int(next(iter(store.query(f"SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{graph}> {{ {pattern} }} }}")))["n"].value)
def node(s): return NamedNode(N+s)
def pred(s): return NamedNode(NS+s)
def entity(q,id,typ,props,graph=GRAPH):
    s=node(id); g=NamedNode(graph)
    q.append(Quad(s,NamedNode(RDF),pred(typ),g))
    for k,v in props.items():
        q.append(Quad(s,pred(k),v if isinstance(v,NamedNode) else Literal(v),g))
def build(source,tax_files):
    full=sections(source["RHSK01"]); excerpt=sections(source["RHSK02"])
    if set(full)!={"任务","话题","词汇","汉字","语法"} or set(excerpt)!={"词汇","汉字","语法"}: raise ValueError("section set")
    wf,we=words(full["词汇"]),words(excerpt["词汇"])
    cf,ce=chars(full["汉字"]),chars(excerpt["汉字"])
    # Cross-excerpt reconciliation preserves differing extractions; no independent evidence promotion.
    wm=[a[0] for a,b in zip(wf,we) if a[:4]!=b[:4] or a[4]!=b[4]+75]
    cm=[a[:3] for a,b in zip(cf,ce) if a[:4]!=b[:4] or a[4]!=b[4]+75]
    if len(cf)!=len(ce): raise ValueError("character count discrepancy")
    b=blocks(full); a=abilities(source["RHSK03"])
    q=[]
    for sid,t in source.items(): entity(q,"source:"+sid,"SourceRecord",{"textSha256":digest(t),"status":"EXTRACTED_TEXT_ONLY"})
    entity(q,"standard:hsk:2025-11","SyllabusVersion",{"releaseLabel":"2025-11","status":"STAGING"})
    for label in ["1","2","3","4","5","6","7","8","9","7-9","1-2"]:
        entity(q,"band:"+label,"LevelBand",{"label":label,"version":node("standard:hsk:2025-11")})
    for i,l,w,r,p in wf:
        entity(q,f"hsk:2025-11:lex:{i}","LexicalRecord",{"ordinal":i,"levelRaw":l,"headwordRaw":w,"readingPosRaw":r,"source":node("source:RHSK01"),"printedPage":p,"levelBand":node("band:"+l.split("（")[0]),"scopeTopic":node("taxonomy:H07.03.03"),"status":"REVIEW_PENDING"})
    chars_seen=set()
    for mode,l,i,c,p in cf:
        cid=f"han:{ord(c):X}"
        if cid not in chars_seen:
            entity(q,cid,"HanCharacter",{"glyph":c}); chars_seen.add(cid)
        entity(q,f"hsk:2025-11:char:{'read' if mode=='认读字' else 'write'}:{l}:{i}","CharacterMembership",{"ordinal":i,"mode":mode,"levelBand":node("band:"+l),"character":node(cid),"scopeTopic":node("taxonomy:H07.03.04"),"source":node("source:RHSK01"),"printedPage":p,"status":"REVIEW_PENDING"})
    for section,l,p,body in b:
        kind={"任务":"Task","话题":"Topic","语法":"Grammar"}[section]
        entity(q,f"hsk:2025-11:block:{kind.lower()}:{p}","SourceBlock",{"blockKind":kind,"levelBand":node("band:"+l),"printedPage":p,"source":node("source:RHSK01"),"rawText":body,"scopeTopic":node("taxonomy:H07.03."+{"Task":"01","Topic":"02","Grammar":"05"}[kind]),"status":"LAYOUT_REVIEW_PENDING"})
    for i,txt in a:
        entity(q,f"hsk:2025-11:ability:{i}","AbilityRecord",{"levelBand":node("band:"+str(i)),"rawText":txt,"scopeTopic":node("taxonomy:H07.02.01"),"source":node("source:RHSK03"),"status":"REVIEW_PENDING"})
    tax_ids={}
    for path in tax_files:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            m=re.match(r"^(?:## |### |- )([KH]\d\d(?:\.\d\d){0,2}) (.+)$",line)
            if not m: continue
            id,label=m.groups()
            if id in tax_ids: raise ValueError("duplicate taxonomy id")
            tax_ids[id]=label
    if len(tax_ids)!=823: raise ValueError("R1 taxonomy inventory mismatch")
    for id,label in tax_ids.items():
        parent=id.rpartition(".")[0]
        if parent and parent not in tax_ids: raise ValueError("missing taxonomy parent")
        entity(q,"taxonomy:"+id,"TaxonomyTopic",{"label":label,"depth":id.count(".")+1,"status":"CANDIDATE",**({"parent":node("taxonomy:"+parent)} if parent else {})},TAX)
    report={"lexical_records":len(wf),"lexical_by_base_band":dict(collections.Counter(x[1].split("（")[0] for x in wf)),"parenthetical_level_records":sum("（" in x[1] for x in wf),"character_memberships":len(cf),"unique_characters":len(chars_seen),"character_by_mode_band":dict(collections.Counter(x[0]+":"+x[1] for x in cf)),"blocks":dict(collections.Counter(x[0] for x in b)),"abilities":len(a),"taxonomy_nodes":len(tax_ids),"word_excerpt_mismatch_count":len(wm),"character_excerpt_mismatch_count":len(cm),"word_excerpt_mismatch_ordinals":wm,"character_excerpt_mismatch_keys":cm,"source_text_sha256":{k:digest(v) for k,v in source.items()}}
    return q,report
def validate(store,report):
    typ=lambda t:f"?s <{RDF}> <{NS+t}>"
    for t,key in [("LexicalRecord","lexical_records"),("HanCharacter","unique_characters"),("CharacterMembership","character_memberships"),("AbilityRecord","abilities")]:
        if query_count(store,typ(t))!=report[key]: raise ValueError("readback "+t)
    if query_count(store,typ("SourceBlock"))!=sum(report["blocks"].values()): raise ValueError("block readback")
    if query_count(store,typ("TaxonomyTopic"),TAX)!=report["taxonomy_nodes"]: raise ValueError("taxonomy readback")
    if query_count(store,f"?s <{RDF}> <{NS}LexicalRecord> ; <{NS}ordinal> 116 ; <{NS}headwordRaw> \"买\" ; <{NS}levelBand> <{N}band:1>")!=1: raise ValueError("buy oracle")
    if query_count(store,f"?s <{RDF}> <{NS}LexicalRecord> ; <{NS}ordinal> 117 ; <{NS}headwordRaw> \"卖\" ; <{NS}levelBand> <{N}band:1>")!=1: raise ValueError("sell oracle")
    linked=int(next(iter(store.query(f"SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{GRAPH}> {{ ?s <{NS}scopeTopic> ?t }} GRAPH <{TAX}> {{ ?t <{RDF}> <{NS}TaxonomyTopic> }} }}")))["n"].value)
    if linked!=report["lexical_records"]+report["character_memberships"]+sum(report["blocks"].values())+report["abilities"]: raise ValueError("cross graph scope link")
    if query_count(store,"?s ?p ?o",N+"graph:accepted")!=0: raise ValueError("accepted leakage")
    if query_count(store,f"?s <{NS}prerequisiteFor> ?o")!=0: raise ValueError("invented prerequisite")
def main():
    p=argparse.ArgumentParser()
    p.add_argument("source",type=Path);p.add_argument("store",type=Path);p.add_argument("--taxonomy",nargs=2,required=True)
    args=p.parse_args()
    if args.store.exists(): raise SystemExit("target exists; use a new immutable staging directory")
    source=json.loads(args.source.read_text(encoding="utf-8"))
    if set(source)!={"RHSK01","RHSK02","RHSK03"}: raise ValueError("unexpected input set")
    q,report=build(source,args.taxonomy)
    parent=args.store.resolve().parent; tmp=Path(tempfile.mkdtemp(prefix=".hsk-import-",dir=parent))
    try:
        s=Store(str(tmp));s.extend(q);validate(s,report); report["quads"]=len(s)
        del s
        s=Store(str(tmp));validate(s,report);del s
        # new target only; rename after validation, not an accepted graph promotion
        tmp.rename(args.store)
    except BaseException:
        shutil.rmtree(tmp,ignore_errors=True);raise
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
