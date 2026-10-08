"""Small, local state machine for multi-dialogue development coordination."""
from __future__ import annotations
import argparse, copy, hashlib, json, os, re, secrets, subprocess, sys, tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA=1
DEFAULT_ROLES={r:0 for r in ("boss","pm","business","engineer","reviewer","release-coordinator")}
MODES={"design","execution"}
SEMVER=re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
SHA=re.compile(r"[0-9a-f]{40}$")
SHA256=re.compile(r"[0-9a-f]{64}$")
ID=re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/@+-]{0,199}$")
LFS_POINTER=re.compile(rb"^version https://git-lfs\.github\.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([1-9][0-9]*)\n$")

class OrchestrationError(Exception): pass
class MutexBusy(OrchestrationError): pass

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def ident(x, label="identifier"):
    if not isinstance(x,str) or not ID.fullmatch(x): raise OrchestrationError(f"Invalid {label}")
    return x
def real_thread(x, label="thread ID"):
    x=ident(x,label)
    if x.lower().startswith(("client:","client-","pending:","operation:","operation-")): raise OrchestrationError(f"{label} must be a confirmed real thread ID")
    return x
def clean(x,label="value"):
    if isinstance(x,str) and ("\x00" in x or "\r" in x or "\n" in x or re.search(r"(?i)(bearer\s+|api[_-]?key|password|secret|token=|sk-[A-Za-z0-9])",x)): raise OrchestrationError(f"{label} contains invalid or secret data")
    return x
def git(root,*args,optional=False):
    r=subprocess.run(["git","-C",str(root),*args],capture_output=True,text=True)
    if r.returncode:
        if optional:return None
        raise OrchestrationError("Git coordination check failed")
    return r.stdout.strip()
def common_dir(root):
    p=Path(git(root,"rev-parse","--git-common-dir")); p=(root/p if not p.is_absolute() else p).resolve(); return p
def state_dir(root):
    return common_dir(root)/".local"/"orchestration"
def state_file(root): return state_dir(root)/"state.json"
def lock_file(root): return state_dir(root)/"state.lock"
def empty(): return {"schema_version":SCHEMA,"updated_at":now(),"tasks":{},"dispatches":{},"publish_lock":None,"audit":[]}
def load(path):
    if not path.exists(): return empty()
    try:v=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,ValueError,UnicodeError) as e: raise OrchestrationError("Orchestration state is unreadable") from e
    if not isinstance(v,dict) or v.get("schema_version")!=SCHEMA or not isinstance(v.get("tasks"),dict) or not isinstance(v.get("dispatches"),dict): raise OrchestrationError("Invalid orchestration state")
    return v
def atomic(path,v):
    path.parent.mkdir(parents=True,exist_ok=True); fd,n=tempfile.mkstemp(prefix=".state-",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8",newline="\n") as f: json.dump(v,f,ensure_ascii=False,indent=2,sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.replace(n,path)
    finally:
        try:os.unlink(n)
        except FileNotFoundError:pass
class Mutex:
    def __init__(self,p):self.p=p; self.t=secrets.token_hex(12)
    def acquire(self):
        self.p.parent.mkdir(parents=True,exist_ok=True)
        try: fd=os.open(self.p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        except FileExistsError as e: raise MutexBusy("Orchestration state is busy") from e
        os.write(fd,json.dumps({"token":self.t,"pid":os.getpid(),"at":now()}).encode()); os.close(fd)
    def release(self):
        try:v=json.loads(self.p.read_text())
        except Exception:return
        if v.get("token")==self.t:
            try:self.p.unlink()
            except FileNotFoundError:pass
@contextmanager
def locked(root):
    m=Mutex(lock_file(root)); m.acquire()
    try:
        s=load(state_file(root)); yield s; s["updated_at"]=now(); atomic(state_file(root),s)
    finally:m.release()
def read_state(root): return copy.deepcopy(load(state_file(root)))
def audit(s,action,actor=None,details=None):
    r={"at":now(),"action":action};
    if actor:r["actor"]=clean(actor,"actor")
    if details:r["details"]=copy.deepcopy(details)
    s.setdefault("audit",[]).append(r); s["audit"]=s["audit"][-500:]
def roles(root):
    p=Path(root)/"docs/development/agent-coverage.json"
    if not p.exists(): return dict(DEFAULT_ROLES)
    try:v=json.loads(p.read_text(encoding="utf-8"))
    except (OSError,ValueError,UnicodeError) as e: raise OrchestrationError("Role coverage file is unreadable") from e
    rows=v.get("roles",v) if isinstance(v,(dict,list)) else []
    out={}
    for row in rows if isinstance(rows,list) else []:
        if isinstance(row,dict) and isinstance(row.get("id"),str):
            stage=row.get("stage", row.get("minimum_stage", 0))
            try: stage=int(str(stage).replace("stage_", "").replace("stage-", ""))
            except (TypeError,ValueError): raise OrchestrationError("Role stage is invalid")
            if stage < 0 or stage > 5: raise OrchestrationError("Role stage is outside 0..5")
            out[row["id"]]=stage
    return out or dict(DEFAULT_ROLES)
def pathnorm(x):
    x=clean(x,"file path"); p=x.replace("\\","/")
    if not p or p.startswith("/") or re.match(r"^[A-Za-z]:/",p) or ".." in p.split("/"): raise OrchestrationError("File ownership paths must be repository-relative")
    return "/".join(a for a in p.split("/") if a not in ("",".")).casefold()
def conflict(a,b): return a==b or a.startswith(b+"/") or b.startswith(a+"/")
def check_files(s,tid,files):
    for oid,t in s["tasks"].items():
        if oid==tid or t.get("ownership_released"):continue
        if any(conflict(a,b) for a in files for b in t.get("file_ownership",[])): raise OrchestrationError(f"File ownership conflicts with task {oid}")
def task(s,tid):
    try:return s["tasks"][ident(tid,"task ID")]
    except KeyError as e:raise OrchestrationError("Task does not exist") from e
def create_task(root,*,task_id,title,parent_task_id,boss_thread_id,pm_thread_id,professional_thread_id,reviewer_thread_id,role,phase,mode,authorization,dependencies=None,branch="",worktree="",baseline_sha="",file_ownership=None,versions=None,contributor_thread_ids=None,author_thread_ids=None,actor=None):
    tid=ident(task_id,"task ID"); phase=int(phase)
    if mode not in MODES:raise OrchestrationError("Mode must be design or execution")
    if mode=="execution" and not authorization.get("execution"):raise OrchestrationError("Execution mode requires explicit authorization")
    if phase==5 and mode=="execution" and not authorization.get("transaction"):raise OrchestrationError("Phase 5 requires transaction authorization")
    role_stages=roles(root)
    if role not in role_stages:raise OrchestrationError("Unknown role ID")
    if phase < 0 or phase > 5:raise OrchestrationError("Phase must be between 0 and 5")
    if mode=="execution" and phase < role_stages[role]:raise OrchestrationError("Role is not enabled at this execution phase")
    for x,l in ((boss_thread_id,"boss ID"),(pm_thread_id,"PM thread ID"),(professional_thread_id,"professional thread ID"),(reviewer_thread_id,"reviewer thread ID")):real_thread(x,l)
    contributors={real_thread(x,"contributor thread ID") for x in (contributor_thread_ids or [])}
    authors={real_thread(x,"author thread ID") for x in (author_thread_ids or [])}
    authors.update(x for x in (authorization.get("strategy_author_thread_id"), authorization.get("experiment_author_thread_id")) if x)
    if reviewer_thread_id in {professional_thread_id} | contributors | authors:
        raise OrchestrationError("Reviewer must be independent of implementer, strategy author, and experiment author")
    deps=[ident(x,"dependency task ID") for x in (dependencies or [])]; files=sorted({pathnorm(x) for x in (file_ownership or [])})
    if baseline_sha and not SHA.fullmatch(baseline_sha):raise OrchestrationError("Baseline must be a full Git SHA")
    with locked(root) as s:
        if tid in s["tasks"]:raise OrchestrationError("Task already exists")
        for d in deps:
            if d not in s["tasks"]:raise OrchestrationError(f"Dependency task {d} is missing")
        check_files(s,tid,files)
        t={"task_id":tid,"title":clean(title,"title"),"parent_task_id":parent_task_id,"participants":{"boss":boss_thread_id,"pm":pm_thread_id,"professional":professional_thread_id},"reviewer_thread_id":reviewer_thread_id,"contributor_thread_ids":sorted(contributors),"author_thread_ids":sorted(authors),"role":role,"authorization":copy.deepcopy(authorization),"dependencies":deps,"phase":phase,"mode":mode,"status":"planned","branch":clean(branch),"worktree":clean(worktree),"baseline_sha":baseline_sha,"file_ownership":files,"ownership_released":False,"versions":copy.deepcopy(versions or {}),"freeze":None,"post_freeze_versions":[],"candidates":[],"current_candidate_id":None,"reviews":[],"cancellation":{"requested":False,"confirmed_stopped":False},"created_at":now(),"updated_at":now()}
        s["tasks"][tid]=t; audit(s,"task_created",actor,{"task_id":tid,"role":role,"mode":mode,"phase":phase}); return copy.deepcopy(t)
def transition(root,tid,action,actor=None):
    allowed={"accept-dependencies":{"planned"},"start":{"ready","returned","insufficient"},"rework":{"returned","insufficient"}}
    if action not in allowed:raise OrchestrationError("Unknown task transition")
    with locked(root) as s:
        t=task(s,tid)
        if t["status"] not in allowed[action]:raise OrchestrationError("Invalid task transition")
        if action=="start" and t.get("cancellation",{}).get("requested"):raise OrchestrationError("Cancelled task cannot start")
        if any(task(s,d)["status"]!="accepted" or task(s,d).get("cancellation",{}).get("requested") for d in t["dependencies"]):raise OrchestrationError("Dependencies have not been accepted or were cancelled")
        t["status"]="ready" if action=="accept-dependencies" else "running"; t["updated_at"]=now(); audit(s,"task_transition",actor,{"task_id":tid,"action":action}); return copy.deepcopy(t)
def freeze(root,tid,*,snapshot_id,as_of,cutoff,summary,actor=None,**versions):
    available_at=versions.pop("available_at",None)
    if not available_at: raise OrchestrationError("Freeze requires available_at")
    try:
        as_of_dt=datetime.fromisoformat(str(as_of).replace("Z","+00:00"))
        available_dt=datetime.fromisoformat(str(available_at).replace("Z","+00:00")); cutoff_dt=datetime.fromisoformat(str(cutoff).replace("Z","+00:00"))
        if as_of_dt.tzinfo is None and "T" in str(as_of): raise ValueError
        if available_dt.tzinfo is None or cutoff_dt.tzinfo is None: raise ValueError
        if available_dt > cutoff_dt: raise ValueError
    except (TypeError,ValueError): raise OrchestrationError("as_of must be ISO date/time; available_at and cutoff must be timezone-aware and ordered")
    f={"snapshot_id":ident(snapshot_id,"snapshot ID"),"as_of":clean(as_of),"available_at":str(available_at),"cutoff":clean(cutoff),"summary":clean(summary),**{k:clean(v) for k,v in versions.items()},"frozen_at":now()}
    with locked(root) as s:
        t=task(s,tid)
        if t["freeze"] is not None:raise OrchestrationError("Pre-market freeze is immutable; create a new version")
        if t["status"] not in {"ready","running"}:raise OrchestrationError("Freeze requires ready or running task")
        t["freeze"]=f; t["versions"].update({k:v for k,v in f.items() if k!="frozen_at"}); audit(s,"task_frozen",actor,{"task_id":tid,"snapshot_id":snapshot_id}); return copy.deepcopy(t)
def post_freeze_version(root,tid,*,snapshot_id,as_of,cutoff,summary,actor=None,**versions):
    v={"snapshot_id":ident(snapshot_id,"snapshot ID"),"as_of":clean(as_of),"cutoff":clean(cutoff),"summary":clean(summary),**{k:clean(x) for k,x in versions.items()},"recorded_at":now()}
    with locked(root) as s:
        t=task(s,tid)
        if t["freeze"] is None:raise OrchestrationError("Post-freeze version requires a freeze")
        if snapshot_id==t["freeze"]["snapshot_id"] or any(v.get("snapshot_id")==snapshot_id for v in t["post_freeze_versions"]): raise OrchestrationError("Post-freeze snapshot ID must be new")
        t["post_freeze_versions"].append(v); audit(s,"post_freeze_version",actor,{"task_id":tid,"snapshot_id":snapshot_id}); return copy.deepcopy(v)
def deliver(root,tid,*,artifact,candidate_id=None,commit_sha="",snapshot_id="",available_at=None,new_version=False,evidence=None,actor=None):
    if commit_sha and not SHA.fullmatch(commit_sha):raise OrchestrationError("Candidate commit must be a full Git SHA")
    if not artifact:raise OrchestrationError("Candidate artifact is required")
    cid=ident(candidate_id,"candidate ID") if candidate_id else "cand-"+secrets.token_hex(8)
    with locked(root) as s:
        t=task(s,tid)
        publish_lock=s.get("publish_lock") or {}; publish_owned=publish_lock.get("task_id")==tid
        if publish_owned and publish_lock.get("final_publish_sha"): raise OrchestrationError("Final publish SHA is already bound")
        if t["status"]!="running" and not (t["status"]=="accepted" and publish_owned):raise OrchestrationError("Candidate delivery requires a running task or an owned publish lock")
        if any(x["candidate_id"]==cid for x in t["candidates"]):raise OrchestrationError("Candidate ID already exists")
        if t["freeze"] is not None:
            if not new_version and snapshot_id!=t["freeze"]["snapshot_id"]:raise OrchestrationError("Frozen task cannot be backfilled")
            if new_version and snapshot_id==t["freeze"]["snapshot_id"]:raise OrchestrationError("New candidate needs a new snapshot ID")
            if new_version and any(c.get("artifact")==artifact and c.get("evidence",{}).get("summary")==((evidence or {}).get("summary")) for c in t["candidates"]):raise OrchestrationError("Post-freeze version must not reuse artifact and summary")
            if not available_at: raise OrchestrationError("Candidate requires available_at evidence")
            effective_cutoff=(evidence or {}).get("cutoff",t["freeze"]["cutoff"])
            if new_version and not (evidence or {}).get("cutoff"): raise OrchestrationError("Post-freeze candidate requires a new cutoff")
            try:
                av=datetime.fromisoformat(str(available_at).replace("Z","+00:00")); co=datetime.fromisoformat(str(effective_cutoff).replace("Z","+00:00"))
                if av.tzinfo is None or co.tzinfo is None or av > co: raise ValueError
            except (TypeError,ValueError): raise OrchestrationError("Candidate available_at is unknown, timezone-naive, or after cutoff")
            nested=(evidence or {}).get("available_at")
            if nested:
                try:
                    nav=datetime.fromisoformat(str(nested).replace("Z","+00:00"))
                    if nav.tzinfo is None or nav > av: raise ValueError
                except (TypeError,ValueError): raise OrchestrationError("Nested evidence available_at is later than outer evidence or invalid")
        c={"candidate_id":cid,"commit_sha":commit_sha,"artifact":clean(artifact),"snapshot_id":snapshot_id or None,"available_at":available_at,"new_version":bool(new_version),"evidence":copy.deepcopy(evidence or {}),"status":"pending_review","delivered_at":now()}
        if publish_owned: c["publish_context"]={k:publish_lock.get(k) for k in ("lock_id","task_id","pm_thread_id","source_candidate_sha","base_sha","version")}; c["publish_context"]["reviewer_thread_id"]=t["reviewer_thread_id"]
        t["candidates"].append(c); t["current_candidate_id"]=cid; t["status"]="delivered"; audit(s,"candidate_delivered",actor,{"task_id":tid,"candidate_id":cid}); return copy.deepcopy(c)
def review(root,tid,*,candidate_id,result,reviewer_thread_id,notes="",actor=None):
    if result not in {"passed","returned","insufficient"}:raise OrchestrationError("Invalid review result")
    reviewer_thread_id=real_thread(reviewer_thread_id,"review thread ID")
    with locked(root) as s:
        t=task(s,tid)
        if t["status"]!="delivered" or t["current_candidate_id"]!=candidate_id:raise OrchestrationError("Review must bind to current candidate")
        if reviewer_thread_id==t["participants"]["professional"]:raise OrchestrationError("Implementer cannot independently review")
        if t.get("reviewer_thread_id")!=reviewer_thread_id or reviewer_thread_id in set(t.get("contributor_thread_ids",[]))|set(t.get("author_thread_ids",[])):raise OrchestrationError("Review must use the task's assigned independent reviewer")
        c=next((x for x in t["candidates"] if x["candidate_id"]==candidate_id),None)
        if not c or c["status"]!="pending_review":raise OrchestrationError("Candidate is not awaiting review")
        r={"candidate_id":candidate_id,"commit_sha":c.get("commit_sha"),"reviewer_thread_id":reviewer_thread_id,"result":result,"notes":clean(notes),"reviewed_at":now()}; c["status"]=result; t["reviews"].append(r); t["status"]="reviewed" if result=="passed" else result; audit(s,"candidate_reviewed",actor,{"task_id":tid,"candidate_id":candidate_id,"result":result}); return copy.deepcopy(r)
def accept(root,tid,*,candidate_id,actor=None):
    with locked(root) as s:
        t=task(s,tid); c=next((x for x in t["candidates"] if x["candidate_id"]==candidate_id),None)
        if t["status"]!="reviewed" or t["current_candidate_id"]!=candidate_id or not c or c["status"]!="passed":raise OrchestrationError("Only a passed current candidate can be accepted")
        t["status"]="accepted"; t["accepted_candidate_snapshot"]={"candidate_id":candidate_id,"commit_sha":c.get("commit_sha"),"artifact":c.get("artifact"),"accepted_at":now()}; audit(s,"task_accepted",actor,{"task_id":tid,"candidate_id":candidate_id}); return copy.deepcopy(t)
def cancel(root,tid,*,reason,actor=None):
    with locked(root) as s:
        t=task(s,tid); t["cancellation"]={"requested":True,"confirmed_stopped":False,"reason":clean(reason),"requested_at":now()}; t["status"]="cancellation_requested"; audit(s,"cancellation_requested",actor,{"task_id":tid}); return copy.deepcopy(t)
def confirm_stop(root,tid,*,actor,evidence=""):
    with locked(root) as s:
        t=task(s,tid)
        if not t["cancellation"].get("requested"):raise OrchestrationError("Cancellation must be requested first")
        if actor!=t["participants"]["professional"] and not isinstance(evidence,dict):raise OrchestrationError("Stop confirmation requires the executor or recovery evidence")
        if isinstance(evidence,dict) and (not evidence.get("recovery_verified") or not evidence.get("thread_or_process_stopped")):raise OrchestrationError("Recovery evidence must verify the thread or process stopped")
        t["cancellation"].update({"confirmed_stopped":True,"confirmed_at":now(),"evidence":clean(evidence)}); t["status"]="confirmed_stopped"; audit(s,"confirmed_stopped",actor,{"task_id":tid}); return copy.deepcopy(t)
def release_files(root,tid,*,actor):
    with locked(root) as s:
        t=task(s,tid)
        if t["status"] not in {"accepted","confirmed_stopped"}:raise OrchestrationError("Ownership remains until acceptance or confirmed stop")
        t["ownership_released"]=True; t["released_at"]=now(); audit(s,"file_ownership_released",actor,{"task_id":tid}); return copy.deepcopy(t)
def dispatch_register(root,*,dispatch_key,task_id,role,operation_id=None,client_thread_id=None,actor=None):
    if role not in roles(root):raise OrchestrationError("Unknown role ID")
    with locked(root) as s:
        task(s,task_id)
        if dispatch_key in s["dispatches"]:raise OrchestrationError("Dispatch key is already used or pending")
        r={"dispatch_key":ident(dispatch_key,"dispatch key"),"task_id":task_id,"role":role,"operation_id":operation_id,"client_thread_id":client_thread_id,"thread_id":None,"status":"pending_creation","created_at":now()}; s["dispatches"][dispatch_key]=r; audit(s,"dispatch_registered",actor,{"dispatch_key":dispatch_key}); return copy.deepcopy(r)

def dispatch_reserve(root,*,dispatch_key,task_id,role,actor=None):
    """Reserve a unique dispatch key before the external create_thread call."""
    return dispatch_register(root,dispatch_key=dispatch_key,task_id=task_id,role=role,actor=actor)

def dispatch_record_result(root,*,dispatch_key,operation_id=None,client_thread_id=None,api_status="returned",actor=None):
    if api_status not in {"returned","error","unknown"}: raise OrchestrationError("Invalid dispatch API status")
    if client_thread_id: ident(client_thread_id,"client thread ID")
    if operation_id: ident(operation_id,"operation ID")
    with locked(root) as s:
        try:r=s["dispatches"][dispatch_key]
        except KeyError as e: raise OrchestrationError("Dispatch key does not exist") from e
        if r["status"]=="confirmed": raise OrchestrationError("Confirmed dispatch cannot be rewritten")
        if r.get("operation_id") or r.get("client_thread_id"):
            if r.get("operation_id")!=operation_id or r.get("client_thread_id")!=client_thread_id: raise OrchestrationError("Dispatch result already recorded; inspect original operation")
            return copy.deepcopy(r)
        r.update({"operation_id":operation_id,"client_thread_id":client_thread_id,"api_status":api_status})
        if api_status in {"error","unknown"}: r["status"]="needs_inspection"
        audit(s,"dispatch_result_recorded",actor,{"dispatch_key":dispatch_key,"api_status":api_status}); return copy.deepcopy(r)
def dispatch_confirm(root,*,dispatch_key,thread_id,actor=None):
    thread_id=real_thread(thread_id)
    with locked(root) as s:
        try:r=s["dispatches"][dispatch_key]
        except KeyError as e:raise OrchestrationError("Dispatch key does not exist") from e
        if r["status"]=="confirmed":
            if r["thread_id"]!=thread_id:raise OrchestrationError("Dispatch already has another thread")
            return copy.deepcopy(r)
        if r["status"]!="pending_creation": raise OrchestrationError("Dispatch result is error/unknown; inspect original operation before retry")
        if r.get("client_thread_id")==thread_id:raise OrchestrationError("Client ID cannot be used as thread ID")
        r.update({"thread_id":thread_id,"status":"confirmed","confirmed_at":now()}); audit(s,"dispatch_confirmed",actor,{"dispatch_key":dispatch_key}); return copy.deepcopy(r)
def remote_main(root,fetch=False):
    if fetch:git(root,"fetch","origin","main")
    sha=git(root,"rev-parse","origin/main")
    if not sha or not SHA.fullmatch(sha):raise OrchestrationError("origin/main is unavailable")
    v=git(root,"show",f"{sha}:VERSION")
    if not v or not SEMVER.fullmatch(v):raise OrchestrationError("origin/main VERSION is invalid")
    a,b,c=map(int,v.split(".")); return sha,v,f"{a}.{b}.{c+1}"
def git_blob(root,sha,path):
    r=subprocess.run(["git","-C",str(root),"show",f"{sha}:{path}"],capture_output=True)
    if r.returncode: raise OrchestrationError("Git coordination check failed")
    return r.stdout
def changed_paths(root,old_sha,new_sha):
    r=subprocess.run(["git","-C",str(root),"diff","--name-only","-z",old_sha,new_sha],capture_output=True)
    if r.returncode: raise OrchestrationError("Git coordination check failed")
    return {p.decode("utf-8") for p in r.stdout.split(b"\0") if p}
def _tree_entries(root,commit):
    r=subprocess.run(["git","-C",str(root),"ls-tree","-r","-z",commit,"--","frontend","desktop","VERSION"],capture_output=True)
    if r.returncode: raise OrchestrationError("Git coordination check failed")
    rows=[]
    for item in r.stdout.split(b"\0"):
        if not item: continue
        head,path=item.split(b"\t",1); mode,kind,blob=head.split()
        if kind!=b"blob" or mode not in {b"100644",b"100755"}: raise OrchestrationError("Canonical source tree contains an unsupported entry")
        rows.append((path.decode("utf-8"),blob.decode("ascii")))
    return rows
def canonical_source_hash(root,commit):
    rows=[]; total=0
    for path,blob in _tree_entries(root,commit):
        parts=path.split("/")
        if any(part in {"node_modules","dist","release","renderer","build","__pycache__"} for part in parts) or path.endswith((".pyc",".tsbuildinfo")): continue
        r=subprocess.run(["git","-C",str(root),"cat-file","blob",blob],capture_output=True)
        if r.returncode: raise OrchestrationError("Git coordination check failed")
        total+=len(r.stdout)
        if len(r.stdout)>8*1024*1024 or total>64*1024*1024: raise OrchestrationError("Canonical source tree is too large")
        rows.append((path,f"{hashlib.sha256(r.stdout).hexdigest()}  {path}\n"))
    return hashlib.sha256("".join(line for _,line in sorted(rows,key=lambda row:row[0].encode("utf-8"))).encode("utf-8")).hexdigest()
def runtime_allowlist(root,source_sha):
    try: raw=git_blob(root,source_sha,"desktop/updater/runtime-files.json")
    except OrchestrationError as exc: raise OrchestrationError("Runtime rebuild requires the canonical runtime file list") from exc
    try: names=json.loads(raw.decode("utf-8"))
    except (UnicodeError,ValueError) as exc: raise OrchestrationError("Canonical runtime file list is invalid") from exc
    if not isinstance(names,list) or not names or any(not isinstance(x,str) or not re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*",x) or any(p in {".",".."} for p in x.split("/")) for x in names): raise OrchestrationError("Canonical runtime file list is invalid")
    out={"desktop-runtime/win-x64/"+x for x in names}
    if len(out)!=len(names): raise OrchestrationError("Canonical runtime file list contains duplicates")
    return out
def lfs_pointer(root,commit,path):
    match=LFS_POINTER.fullmatch(git_blob(root,commit,path))
    if not match: raise OrchestrationError(f"Runtime file is not a valid Git LFS pointer: {path}")
    return match.group(1).decode("ascii"),int(match.group(2))
def runtime_tree(root,commit):
    rows=git(root,"ls-tree","-r","-z",commit,"--","desktop-runtime").split("\0")
    files=set()
    for row in rows:
        if not row: continue
        metadata,path=row.split("\t",1)
        if metadata.split()[:2]!=["100644","blob"]: raise OrchestrationError("Runtime tree must contain regular non-executable LFS pointer files")
        files.add(path)
    return files
def verify_local_lfs_object(root,oid,size):
    obj=common_dir(root)/"lfs"/"objects"/oid[:2]/oid[2:4]/oid
    if obj.is_symlink() or not obj.is_file() or obj.stat().st_size!=size: raise OrchestrationError("Local LFS object is missing or has the wrong byte size")
    digest=hashlib.sha256()
    with obj.open("rb") as source:
        for chunk in iter(lambda:source.read(1024*1024),b""): digest.update(chunk)
    if digest.hexdigest()!=oid: raise OrchestrationError("Local LFS object digest does not match the candidate pointer")
def validate_runtime_candidate(root,old_sha,candidate_sha,version,evidence):
    changed=changed_paths(root,old_sha,candidate_sha); runtime={p for p in changed if p.startswith("desktop-runtime/")}
    if not runtime: raise OrchestrationError("Source rebind requires a runtime rebuild candidate")
    if "VERSION" not in changed or git(root,"show",f"{candidate_sha}:VERSION") != version: raise OrchestrationError("Runtime rebuild candidate must bump VERSION to the locked version")
    allowed={"VERSION","CHANGELOG.md",f"docs/releases/{version}.md",f"docs/releases/{version}.json"}|runtime
    if not changed.issubset(allowed): raise OrchestrationError("Runtime candidate changes files outside release materials and explicitly listed runtime files")
    d=evidence.get("desktop_runtime") if isinstance(evidence,dict) else None
    required=("verifier","verified","rebuilt","manifest_reused","build_source_sha","source_tree_hash","manifest_path","manifest_lfs_oid","manifest_size","manifest_content","runtime_file_count","lfs_objects_verified","lfs_objects")
    if not isinstance(d,dict) or any(k not in d for k in required) or d.get("verifier")!="verify_desktop_runtime" or d.get("verified") is not True or d.get("rebuilt") is not True or d.get("manifest_reused") is not False or d.get("lfs_objects_verified") is not True: raise OrchestrationError("Runtime candidate requires a complete verified rebuild receipt")
    paths=d.get("paths")
    if not isinstance(paths,list) or any(not isinstance(p,str) for p in paths) or len(paths)!=len(set(paths)) or set(paths)!=runtime: raise OrchestrationError("Runtime evidence must enumerate the exact changed runtime files")
    build_source=d.get("build_source_sha"); source_tree=d.get("source_tree_hash")
    if not SHA.fullmatch(str(build_source)) or not SHA256.fullmatch(str(source_tree)): raise OrchestrationError("Runtime build source or canonical source hash is invalid")
    if git(root,"merge-base","--is-ancestor",build_source,candidate_sha,optional=True) is None: raise OrchestrationError("Build source must be an ancestor of the runtime candidate")
    if git(root,"show",f"{build_source}:VERSION") != version: raise OrchestrationError("Build source VERSION does not match the locked version")
    content=d.get("manifest_content")
    if not isinstance(content,str) or len(content.encode("utf-8"))!=d.get("manifest_size") or hashlib.sha256(content.encode("utf-8")).hexdigest()!=d.get("manifest_lfs_oid"): raise OrchestrationError("Runtime manifest content does not match its LFS object")
    try: m=json.loads(content)
    except ValueError as exc: raise OrchestrationError("Runtime build manifest is invalid JSON") from exc
    fields={"schema","repository","version","build_source_sha","source_tree_hash","platform","arch"}
    if not isinstance(m,dict) or set(m)!=fields or type(m.get("schema")) is not int or m.get("schema")!=1 or m.get("repository")!="MrLaoGe/x2Stock" or m.get("version")!=version or m.get("build_source_sha")!=build_source or m.get("source_tree_hash")!=source_tree or m.get("platform")!="win32" or m.get("arch")!="x64": raise OrchestrationError("Runtime build manifest is inconsistent with the lock")
    if canonical_source_hash(root,build_source)!=source_tree: raise OrchestrationError("Runtime receipt source_tree_hash does not match the clean build source")
    if canonical_source_hash(root,candidate_sha)!=source_tree: raise OrchestrationError("Runtime candidate source tree differs from the build source")
    allowed_runtime=runtime_allowlist(root,old_sha)
    if len(allowed_runtime)!=73 or runtime_tree(root,candidate_sha)!=allowed_runtime: raise OrchestrationError("Runtime candidate must contain exactly the 73 canonical runtime files")
    if not runtime.issubset(allowed_runtime) or "desktop-runtime/win-x64/resources/build-manifest.json" not in runtime: raise OrchestrationError("Runtime changes must be a subset of the canonical runtime file list and include build-manifest.json")
    if d.get("runtime_file_count")!=len(allowed_runtime): raise OrchestrationError("Runtime receipt does not account for every canonical runtime object")
    pointer_oids={}
    for path in allowed_runtime:
        pointer_oids[path]=lfs_pointer(root,candidate_sha,path)
        verify_local_lfs_object(root,*pointer_oids[path])
    expected_objects={path:{"oid":oid,"size":size} for path,(oid,size) in pointer_oids.items()}
    if d.get("lfs_objects")!=expected_objects: raise OrchestrationError("Runtime receipt LFS objects do not match every candidate pointer")
    manifest_path=d.get("manifest_path")
    if manifest_path!="desktop-runtime/win-x64/resources/build-manifest.json" or manifest_path not in runtime: raise OrchestrationError("Runtime receipt must identify the canonical build manifest")
    manifest_oid,manifest_size=pointer_oids[manifest_path]
    if d.get("manifest_lfs_oid")!=manifest_oid or d.get("manifest_size")!=manifest_size: raise OrchestrationError("Runtime manifest LFS pointer does not match the reviewed receipt")
    return changed
def acquire_lock(root,*,task_id,pm_thread_id,candidate_id,expected_version=None,fetch=False,actor=None):
    pm_thread_id=real_thread(pm_thread_id,"PM thread ID"); base,old,nxt=remote_main(root,fetch)
    if expected_version and expected_version!=nxt:raise OrchestrationError("Publish version is stale")
    with locked(root) as s:
        t=task(s,task_id)
        if t["participants"]["pm"]!=pm_thread_id:raise OrchestrationError("Publish PM does not match task PM")
        if t["status"]!="accepted" or t.get("current_candidate_id")!=candidate_id:raise OrchestrationError("Publish lock requires the accepted current candidate")
        candidate=next((c for c in t["candidates"] if c["candidate_id"]==candidate_id),None)
        if not candidate or candidate.get("status")!="passed":raise OrchestrationError("Publish lock requires independent review evidence")
        if t.get("baseline_sha") != base:raise OrchestrationError("Task baseline must equal latest origin/main")
        if not candidate.get("commit_sha") or git(root,"merge-base","--is-ancestor",base,candidate["commit_sha"],optional=True) is None:raise OrchestrationError("Candidate does not contain latest origin/main")
        evidence=candidate.get("evidence",{})
        if evidence.get("integrated_base_sha")!=base or evidence.get("integration_verified") is not True:raise OrchestrationError("Candidate lacks verified integration evidence")
        if s.get("publish_lock"):raise OrchestrationError("Another PM holds publish lock; no timeout takeover")
        l={"lock_id":"lock-"+secrets.token_hex(12),"task_id":task_id,"pm_thread_id":pm_thread_id,"candidate_id":candidate_id,"source_candidate_sha":candidate.get("commit_sha"),"baseline_sha":t.get("baseline_sha"),"base_sha":base,"remote_version":old,"version":nxt,"coordination_version":nxt,"runtime_review_sha":None,"final_publish_sha":None,"final_publish_version":None,"holder_status":"held","acquired_at":now()}; s["publish_lock"]=l; audit(s,"publish_lock_acquired",actor,{"task_id":task_id,"version":nxt,"candidate_id":candidate_id,"lock_id":l["lock_id"]}); return copy.deepcopy(l)
def rebind_publish_source(root,*,task_id,pm_thread_id,candidate_id,fetch=False,actor=None):
    pm_thread_id=real_thread(pm_thread_id,"PM thread ID")
    base,old,nxt=remote_main(root,fetch)
    with locked(root) as s:
        l=s.get("publish_lock")
        if not l or l["task_id"]!=task_id or l["pm_thread_id"]!=pm_thread_id: raise OrchestrationError("Only lock owner may rebind source candidate")
        if l.get("final_publish_sha"): raise OrchestrationError("Final publish SHA is already bound")
        t=task(s,task_id)
        if not l.get("lock_id") or (base,old,nxt)!=(l.get("base_sha"),l.get("remote_version"),l.get("version")) or t.get("baseline_sha")!=base: raise OrchestrationError("Source rebind requires the locked latest main baseline and version")
        if t["participants"]["pm"]!=pm_thread_id or t.get("cancellation",{}).get("requested"): raise OrchestrationError("Rebind task PM or cancellation state is invalid")
        if t.get("status")!="accepted" or t.get("current_candidate_id")!=candidate_id: raise OrchestrationError("Rebind requires a newly reviewed accepted current candidate")
        c=next((x for x in t.get("candidates",[]) if x.get("candidate_id")==candidate_id),None)
        if not c or c.get("status")!="passed" or not c.get("commit_sha") or git(root,"merge-base","--is-ancestor",l["base_sha"],c["commit_sha"],optional=True) is None: raise OrchestrationError("Rebind candidate does not contain locked latest main")
        context=c.get("publish_context",{})
        if any(context.get(k)!=l.get(k) for k in ("lock_id","task_id","pm_thread_id","base_sha","version","source_candidate_sha")) or context.get("reviewer_thread_id")!=t.get("reviewer_thread_id"): raise OrchestrationError("Rebind candidate is not bound to this lock, PM, version, source, and reviewer")
        if git(root,"merge-base","--is-ancestor",l["source_candidate_sha"],c["commit_sha"],optional=True) is None: raise OrchestrationError("Rebind candidate must contain the previously accepted source candidate")
        snapshot=t.get("accepted_candidate_snapshot",{})
        if snapshot.get("candidate_id")!=candidate_id or snapshot.get("commit_sha")!=c["commit_sha"] or not any(r.get("candidate_id")==candidate_id and r.get("commit_sha")==c["commit_sha"] and r.get("reviewer_thread_id")==t["reviewer_thread_id"] and r.get("result")=="passed" for r in t.get("reviews",[])): raise OrchestrationError("Rebind requires exact SHA acceptance and assigned independent review")
        d=c.get("evidence",{}).get("desktop_runtime",{})
        receipt_context={**context,"candidate_sha":c["commit_sha"],"candidate_id":candidate_id}
        if not isinstance(d,dict) or d.get("review_binding")!=receipt_context: raise OrchestrationError("Runtime verifier receipt is not bound to the exact candidate and review context")
        if c.get("evidence",{}).get("integrated_base_sha")!=l["base_sha"] or c.get("evidence",{}).get("integration_verified") is not True: raise OrchestrationError("Rebind candidate lacks verified integration evidence")
        validate_runtime_candidate(root,l["source_candidate_sha"],c["commit_sha"],l["version"],c.get("evidence",{}))
        if remote_main(root,False)!=(base,old,nxt): raise OrchestrationError("origin/main changed while validating the runtime candidate")
        l.setdefault("source_rebindings",[]).append({"from_sha":l["source_candidate_sha"],"to_sha":c["commit_sha"],"candidate_id":candidate_id,"reviewer_thread_id":t["reviewer_thread_id"],"lock_id":l["lock_id"],"version":l["version"],"base_sha":base,"at":now()})
        l.update({"candidate_id":candidate_id,"source_candidate_sha":c["commit_sha"],"runtime_review_sha":c["commit_sha"],"holder_status":"held"}); audit(s,"publish_source_rebound",actor,{"task_id":task_id,"candidate_id":candidate_id,"source_candidate_sha":c["commit_sha"],"runtime_review_sha":c["commit_sha"]}); return copy.deepcopy(l)
def bind_publish_final(root,*,task_id,pm_thread_id,final_publish_sha,version,actor=None):
    if not SHA.fullmatch(final_publish_sha) or not SEMVER.fullmatch(version): raise OrchestrationError("Final publish SHA/version is invalid")
    with locked(root) as s:
        l=s.get("publish_lock")
        if not l or l["task_id"]!=task_id or l["pm_thread_id"]!=pm_thread_id: raise OrchestrationError("Only lock owner may bind final publish SHA")
        if version!=l["version"]: raise OrchestrationError("Final publish version does not match lock")
        if l.get("final_publish_sha"):
            if l["final_publish_sha"]==final_publish_sha and l.get("final_publish_version")==version: return copy.deepcopy(l)
            raise OrchestrationError("Final publish SHA is already bound and cannot be replaced")
        t=task(s,task_id)
        if t.get("status")!="accepted" or t.get("current_candidate_id")!=l.get("candidate_id") or t.get("cancellation",{}).get("requested"): raise OrchestrationError("Final binding requires the lock's accepted current candidate")
        if git(root,"merge-base","--is-ancestor",l["source_candidate_sha"],final_publish_sha,optional=True) is None: raise OrchestrationError("Final publish SHA does not contain source candidate")
        if l.get("runtime_review_sha") and final_publish_sha!=l["runtime_review_sha"]: raise OrchestrationError("Final publish must equal the exact runtime review SHA")
        if git(root,"show",f"{final_publish_sha}:VERSION") != version: raise OrchestrationError("Final publish VERSION does not match lock")
        allowed={"VERSION","CHANGELOG.md",f"docs/releases/{version}.md",f"docs/releases/{version}.json"}
        changed=changed_paths(root,l["source_candidate_sha"],final_publish_sha)
        if runtime_tree(root,l["source_candidate_sha"]) and (not l.get("runtime_review_sha") or "VERSION" in changed): raise OrchestrationError("Existing runtime requires rebuilding and exact candidate review before final binding")
        if any(p.startswith("desktop-runtime/") for p in changed): raise OrchestrationError("Runtime changes require a reviewed source rebind before final binding")
        if not changed.issubset(allowed): raise OrchestrationError("Final publish commit changes files outside release-material allowlist")
        l["final_publish_sha"]=final_publish_sha; l["final_publish_version"]=version; l["holder_status"]="final_bound"; audit(s,"publish_final_bound",actor,{"task_id":task_id,"final_publish_sha":final_publish_sha,"version":version}); return copy.deepcopy(l)
def release_lock(root,*,task_id,pm_thread_id,actor=None):
    with locked(root) as s:
        l=s.get("publish_lock")
        if not l or l["task_id"]!=task_id or l["pm_thread_id"]!=pm_thread_id:raise OrchestrationError("Only lock owner may release")
        t=task(s,task_id)
        if t.get("status")!="accepted" or t.get("current_candidate_id")!=l.get("candidate_id"): raise OrchestrationError("Lock can only be released from the accepted current candidate")
        if l.get("runtime_review_sha") and l.get("runtime_review_sha")!=l.get("source_candidate_sha"): raise OrchestrationError("Runtime source rebind is incomplete")
        s["publish_lock"]=None; audit(s,"publish_lock_released",actor,{"task_id":task_id})
def recover_lock(root,*,task_id,pm_thread_id,coordinator_id,evidence,actor=None):
    if not isinstance(evidence,dict) or evidence.get("holder_status") not in {"stopped","failed"} or not evidence.get("mutex_recovered") or not SHA.fullmatch(str(evidence.get("exact_sha",""))) or not SEMVER.fullmatch(str(evidence.get("version",""))) or evidence.get("actions") not in {"completed","failed"} or any(not isinstance(evidence.get(k),dict) or evidence[k].get("status") not in {"completed","failed","absent"} for k in ("remote_git","tag","release","notification")):
        raise OrchestrationError("Recovery requires structured terminal evidence with exact SHA and version")
    with locked(root) as s:
        l=s.get("publish_lock")
        if not l or l["task_id"]!=task_id or l["pm_thread_id"]!=pm_thread_id:raise OrchestrationError("Recovery target does not match lock")
        expected_sha=l.get("final_publish_sha") or l.get("source_candidate_sha")
        if evidence.get("exact_sha")!=expected_sha or evidence.get("version")!=l.get("version") or evidence.get("candidate_sha")!=l.get("source_candidate_sha"): raise OrchestrationError("Recovery evidence does not match source/final SHA or version")
        if not l.get("final_publish_sha") and (evidence.get("not_published") is not True or evidence.get("pending_version_absent") is not True or any(evidence[key].get("status") not in {"absent","failed"} for key in ("remote_git","tag","release","notification"))):
            raise OrchestrationError("Unbound recovery requires verified not-published and absent pending version")
        for key in ("remote_git","tag","release","notification"):
            if evidence[key].get("status")=="completed" and (evidence[key].get("sha")!=evidence.get("exact_sha") or evidence[key].get("version")!=evidence.get("version")): raise OrchestrationError("Completed recovery evidence requires matching SHA and version")
        s["publish_lock"]=None; audit(s,"publish_lock_recovered",actor or coordinator_id,{"task_id":task_id,"coordinator_id":coordinator_id,"evidence":copy.deepcopy(evidence)})

def recover_mutex(root,*,evidence):
    """Explicitly clear a leftover O_EXCL mutex after a crashed process."""
    if not isinstance(evidence,dict) or evidence.get("holder_status") not in {"stopped","failed"} or not evidence.get("mutex_recovered") or not evidence.get("mutex_token") or not evidence.get("mutex_pid"):
        raise OrchestrationError("Mutex recovery requires stopped/failed holder, token, and explicit evidence")
    path=lock_file(root)
    try: current=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,ValueError,UnicodeError) as exc: raise OrchestrationError("Mutex evidence does not match a readable lock") from exc
    if current.get("token")!=evidence["mutex_token"]: raise OrchestrationError("Mutex token mismatch")
    if current.get("pid")!=evidence["mutex_pid"]: raise OrchestrationError("Mutex pid mismatch")
    pid=int(current["pid"])
    if os.name == "nt":
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION=0x1000; STILL_ACTIVE=259
        kernel=ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong]; kernel.OpenProcess.restype=ctypes.c_void_p
        kernel.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ulong)]; kernel.GetExitCodeProcess.restype=ctypes.c_int
        kernel.CloseHandle.argtypes=[ctypes.c_void_p]; kernel.CloseHandle.restype=ctypes.c_int
        handle=kernel.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION,False,pid)
        if handle:
            code=ctypes.c_ulong(); ok=kernel.GetExitCodeProcess(handle,ctypes.byref(code)); kernel.CloseHandle(handle)
            if not ok: raise OrchestrationError("Mutex owner state is unknown; no timeout recovery")
            if code.value==STILL_ACTIVE: raise OrchestrationError("Mutex owner is still live; no timeout recovery")
        else:
            error=ctypes.get_last_error()
            if pid == os.getpid() or error != 87: raise OrchestrationError("Mutex owner state is unknown; no timeout recovery")
    else:
        try: os.kill(pid,0)
        except ProcessLookupError: pass
        except PermissionError: raise OrchestrationError("Mutex owner is still live or cannot be checked")
        else: raise OrchestrationError("Mutex owner is still live; no timeout recovery")
    path.unlink()

def main(argv=None,root=None):
    root=Path(root or Path(__file__).resolve().parents[4]); p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="c",required=True); sub.add_parser("show")
    x=sub.add_parser("task-create");
    for n in ("task-id","title","boss","pm","professional","reviewer","role","mode","authorization"):x.add_argument("--"+n,required=True)
    x.add_argument("--phase",type=int,required=True); x.add_argument("--parent",default=""); x.add_argument("--baseline",default=""); x.add_argument("--worktree",default=""); x.add_argument("--branch",default=""); x.add_argument("--dependencies",default="[]"); x.add_argument("--files",default="[]"); x.add_argument("--contributors",default="[]"); x.add_argument("--authors",default="[]"); x.add_argument("--versions",default="{}")
    x=sub.add_parser("task-transition");x.add_argument("task_id");x.add_argument("action")
    x=sub.add_parser("task-freeze");x.add_argument("task_id");x.add_argument("--snapshot-id",required=True);x.add_argument("--as-of",required=True);x.add_argument("--available-at",required=True);x.add_argument("--cutoff",required=True);x.add_argument("--summary",required=True)
    x=sub.add_parser("task-post-freeze-version");x.add_argument("task_id");x.add_argument("--snapshot-id",required=True);x.add_argument("--as-of",required=True);x.add_argument("--cutoff",required=True);x.add_argument("--summary",required=True);x.add_argument("--versions",default="{}")
    x=sub.add_parser("task-deliver");x.add_argument("task_id");x.add_argument("--artifact",required=True);x.add_argument("--candidate-id");x.add_argument("--commit-sha",default="");x.add_argument("--snapshot-id",default="");x.add_argument("--available-at");x.add_argument("--new-version",action="store_true");x.add_argument("--evidence",default="{}")
    x=sub.add_parser("task-review");x.add_argument("task_id");x.add_argument("--candidate-id",required=True);x.add_argument("--result",required=True);x.add_argument("--reviewer",required=True)
    x=sub.add_parser("task-accept");x.add_argument("task_id");x.add_argument("--candidate-id",required=True)
    x=sub.add_parser("task-cancel");x.add_argument("task_id");x.add_argument("--reason",required=True)
    x=sub.add_parser("task-stop");x.add_argument("task_id");x.add_argument("--actor",required=True);x.add_argument("--evidence",default="")
    x=sub.add_parser("task-release-files");x.add_argument("task_id");x.add_argument("--actor",required=True)
    x=sub.add_parser("publish-lock-recover");x.add_argument("--task-id",required=True);x.add_argument("--pm",required=True);x.add_argument("--coordinator",required=True);x.add_argument("--evidence",required=True)
    x=sub.add_parser("dispatch-register");x.add_argument("--dispatch-key",required=True);x.add_argument("--task-id",required=True);x.add_argument("--role",required=True);x.add_argument("--client-thread-id");x.add_argument("--operation-id")
    x=sub.add_parser("dispatch-reserve");x.add_argument("--dispatch-key",required=True);x.add_argument("--task-id",required=True);x.add_argument("--role",required=True)
    x=sub.add_parser("dispatch-record-result");x.add_argument("--dispatch-key",required=True);x.add_argument("--operation-id");x.add_argument("--client-thread-id");x.add_argument("--api-status",default="returned")
    x=sub.add_parser("dispatch-confirm");x.add_argument("--dispatch-key",required=True);x.add_argument("--thread-id",required=True)
    x=sub.add_parser("publish-lock-acquire");x.add_argument("--task-id",required=True);x.add_argument("--pm",required=True);x.add_argument("--candidate-id",required=True);x.add_argument("--expected-version");x.add_argument("--no-fetch",action="store_true")
    x=sub.add_parser("publish-lock-rebind-source");x.add_argument("--task-id",required=True);x.add_argument("--pm",required=True);x.add_argument("--candidate-id",required=True);x.add_argument("--no-fetch",action="store_true")
    x=sub.add_parser("publish-lock-bind-final");x.add_argument("--task-id",required=True);x.add_argument("--pm",required=True);x.add_argument("--publish-sha",required=True);x.add_argument("--version",required=True)
    x=sub.add_parser("publish-lock-release");x.add_argument("--task-id",required=True);x.add_argument("--pm",required=True)
    x=sub.add_parser("mutex-recover");x.add_argument("--evidence",required=True)
    a=p.parse_args(argv)
    try:
        if a.c=="show":r=read_state(root)
        elif a.c=="task-create":r=create_task(root,task_id=a.task_id,title=a.title,parent_task_id=a.parent,boss_thread_id=a.boss,pm_thread_id=a.pm,professional_thread_id=a.professional,reviewer_thread_id=a.reviewer,role=a.role,phase=a.phase,mode=a.mode,authorization=json.loads(a.authorization),dependencies=json.loads(a.dependencies),file_ownership=json.loads(a.files),baseline_sha=a.baseline,worktree=a.worktree,branch=a.branch,contributor_thread_ids=json.loads(a.contributors),author_thread_ids=json.loads(a.authors),versions=json.loads(a.versions))
        elif a.c=="task-transition":r=transition(root,a.task_id,a.action)
        elif a.c=="task-freeze":r=freeze(root,a.task_id,snapshot_id=a.snapshot_id,as_of=a.as_of,available_at=a.available_at,cutoff=a.cutoff,summary=a.summary)
        elif a.c=="task-post-freeze-version":r=post_freeze_version(root,a.task_id,snapshot_id=a.snapshot_id,as_of=a.as_of,cutoff=a.cutoff,summary=a.summary,**json.loads(a.versions))
        elif a.c=="task-deliver":r=deliver(root,a.task_id,artifact=a.artifact,candidate_id=a.candidate_id,commit_sha=a.commit_sha,snapshot_id=a.snapshot_id,available_at=a.available_at,new_version=a.new_version,evidence=json.loads(a.evidence))
        elif a.c=="task-review":r=review(root,a.task_id,candidate_id=a.candidate_id,result=a.result,reviewer_thread_id=a.reviewer)
        elif a.c=="task-accept":r=accept(root,a.task_id,candidate_id=a.candidate_id)
        elif a.c=="task-cancel":r=cancel(root,a.task_id,reason=a.reason)
        elif a.c=="task-stop":r=confirm_stop(root,a.task_id,actor=a.actor,evidence=json.loads(a.evidence) if a.evidence else "")
        elif a.c=="task-release-files":r=release_files(root,a.task_id,actor=a.actor)
        elif a.c=="dispatch-register":r=dispatch_register(root,dispatch_key=a.dispatch_key,task_id=a.task_id,role=a.role,client_thread_id=a.client_thread_id,operation_id=a.operation_id)
        elif a.c=="dispatch-reserve":r=dispatch_reserve(root,dispatch_key=a.dispatch_key,task_id=a.task_id,role=a.role)
        elif a.c=="dispatch-record-result":r=dispatch_record_result(root,dispatch_key=a.dispatch_key,operation_id=a.operation_id,client_thread_id=a.client_thread_id,api_status=a.api_status)
        elif a.c=="dispatch-confirm":r=dispatch_confirm(root,dispatch_key=a.dispatch_key,thread_id=a.thread_id)
        elif a.c=="publish-lock-acquire":r=acquire_lock(root,task_id=a.task_id,pm_thread_id=a.pm,candidate_id=a.candidate_id,expected_version=a.expected_version,fetch=not a.no_fetch)
        elif a.c=="publish-lock-rebind-source":r=rebind_publish_source(root,task_id=a.task_id,pm_thread_id=a.pm,candidate_id=a.candidate_id,fetch=not a.no_fetch)
        elif a.c=="publish-lock-bind-final":r=bind_publish_final(root,task_id=a.task_id,pm_thread_id=a.pm,final_publish_sha=a.publish_sha,version=a.version)
        elif a.c=="publish-lock-recover":r=recover_lock(root,task_id=a.task_id,pm_thread_id=a.pm,coordinator_id=a.coordinator,evidence=json.loads(a.evidence)) or {"recovered":True}
        elif a.c=="mutex-recover":r=recover_mutex(root,evidence=json.loads(a.evidence)) or {"recovered":True}
        else:r=release_lock(root,task_id=a.task_id,pm_thread_id=a.pm) or {"released":True}
        print(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)); return 0
    except (OrchestrationError,ValueError,TypeError) as e: print(f"Orchestration failed: {e}",file=sys.stderr); return 1
if __name__=="__main__":raise SystemExit(main())
