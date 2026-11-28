"""Candidate process pointer with an explicit, hash-bound IF01 relation-extension pin. Original DB02 pointer unchanged."""
import fcntl
import os
import pathlib
import tempfile
from tools.knowledge_import.importer import Importer, ManifestPin, Reject, canonical, parse, need

def read_pointer(directory):
    p = pathlib.Path(directory)/"candidate-current.json"
    if not p.exists():
        return None
    need(not p.is_symlink(), "POINTER_SYMLINK")
    x = parse(p.read_bytes())
    need(isinstance(x,dict) and set(x)=={"mode","select","catalog","extension"} and x["mode"]=="CANDIDATE_RESEARCH_ONLY", "POINTER_SCOPE")
    return x

def resolve(snapshot, root):
    need(isinstance(snapshot,dict) and set(snapshot)=={"mode","select","catalog","extension"} and snapshot.get("mode")=="CANDIDATE_RESEARCH_ONLY","POINTER_SCOPE")
    extension=snapshot["extension"]
    need(type(extension) is list and len(extension)==2 and all(type(x) is str and x for x in extension),"POINTER_EXTENSION")
    need(extension[0]=="knowledge/v0.1.0/foundation-r3/relation-types.json","POINTER_EXTENSION_PATH")
    need(type(snapshot["select"]) is list and len(snapshot["select"])==2 and snapshot["select"][0]=="learning-process" and snapshot["select"][1] in ("0.1.0-process-candidate-3","0.1.0-process-candidate-4"),"POINTER_PROCESS_TUPLE")
    catalog={}
    for p,v,path,sha in snapshot["catalog"]:
        need((p,v) not in catalog,"DUPLICATE_CATALOG")
        catalog[p,v]=ManifestPin(path,sha)
    im=Importer(root, mode="research", catalog=catalog, extension=ManifestPin(*extension))
    try:return im.run(tuple(snapshot["select"]))
    finally:im.close()

def switch(directory, root, snapshot, expected, *, _crash=None):
    """CAS, validate all selected bytes, fsync pointer then atomic rename, sync parent.
    _crash is a test hook; process death is not a physical power-loss guarantee.
    """
    d=pathlib.Path(directory)
    need(d.is_dir() and not d.is_symlink(),"POINTER_DIRECTORY")
    lock=d/"candidate.lock"
    with os.fdopen(os.open(lock,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600),"r+b") as f:
        fcntl.flock(f,fcntl.LOCK_EX)
        need(read_pointer(d)==expected,"POINTER_CAS")
        resolve(snapshot,root)
        fd, temp=tempfile.mkstemp(prefix=".candidate-",dir=d)
        try:
            with os.fdopen(fd,"wb") as tmp:
                tmp.write(canonical(snapshot).encode("utf-8"))
                tmp.flush();os.fsync(tmp.fileno())
            if _crash=="before_replace":os._exit(71)
            os.replace(temp,d/"candidate-current.json")
            if _crash=="after_replace":os._exit(72)
            dfd=os.open(d,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(dfd)
            finally:os.close(dfd)
        finally:
            if os.path.exists(temp):os.unlink(temp)
