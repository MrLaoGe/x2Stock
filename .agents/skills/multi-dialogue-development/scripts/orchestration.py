"""Small, local state machine for multi-dialogue development coordination."""
from __future__ import annotations
import argparse, copy, json, os, re, secrets, subprocess, sys, tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA=1
DEFAULT_ROLES={"boss","pm","business","engineer","reviewer","release-coordinator"}
MODES={"design","execution"}
SEMVER=re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
SHA=re.compile(r"[0-9a-f]{40}$")
ID=re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/@+-]{0,199}$")

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
    if not p.exists(): return DEFAULT_ROLES
    try:v=json.loads(p.read_text(encoding="utf-8"))
    except (OSError,ValueError,UnicodeError) as e: raise OrchestrationError("Role coverage file is unreadable") from e
    rows=v.get("roles",v) if isinstance(v,(dict,list)) else []
    out={}
    for row in rows if isinstance(rows,list) else []:
        if isinstance(row,dict) and isinstance(row.get("id"),str):
            stage=row.get("stage", row.get("minimum_stage", 0))
            try: stage=int(stage)
            except (TypeError,ValueError): raise OrchestrationError("Role stage is invalid")
            if stage < 0 or stage > 5: raise OrchestrationError("Role stage is outside 0..5")
            out[row["id"]]=stage
    return out or {role: 0 for role in DEFAULT_ROLES}
def pathnorm(x):
    x=clean(x,"file path"); p=x.replace("\\","/")
    if not p or p.startswith("/") or re.match(r"^[A-Za-z]:/",p) or ".." in p.split("/"): raise OrchestrationError("File ownership paths must be repository-relative")
    return "/".join(a for a in p.split("/") if a not in ("","."))
def conflict(a,b): return a==b or a.startswith(b+"/") or b.startswith(a+"/")
def check_files(s,tid,files):
    for oid,t in s["tasks"].items():
        if oid==tid or t.get("ownership_released"):continue
        if any(conflict(a,b) for a in files for b in t.get("file_ownership",[])): raise OrchestrationError(f"File ownership conflicts with task {oid}")
def task(s,tid):
    try:return s["tasks"][ident(tid,"task ID")]
    except KeyError as e:raise OrchestrationError("Task does not exist") from e
def create_task(root,*,task_id,title,parent_task_id,boss_thread_id,pm_thread_id,professional_thread_id,role,phase,mode,authorization,dependencies=None,branch="",worktree="",baseline_sha="",file_ownership=None,versions=None,actor=None):
    tid=ident(task_id,"task ID"); phase=int(phase)
    if mode not in MODES:raise OrchestrationError("Mode must be design or execution")
    if mode=="execution" and not authorization.get("execution"):raise OrchestrationError("Execution mode requires explicit authorization")
    if phase==5 and mode=="execution" and not authorization.get("transaction"):raise OrchestrationError("Phase 5 requires transaction authorization")
    role_stages=roles(root)
    if role not in role_stages:raise OrchestrationError("Unknown role ID")
    if phase < 0 or phase > 5:raise OrchestrationError("Phase must be between 0 and 5")
    if mode=="execution" and phase < role_stages[role]:raise OrchestrationError("Role is not enabled at this execution phase")
    for x,l in ((boss_thread_id,"boss ID"),(pm_thread_id,"PM thread ID"),(professional_thread_id,"professional thread ID")):real_thread(x,l)
    deps=[ident(x,"dependency task ID") for x in (dependencies or [])]; files=sorted({pathnorm(x) for x in (file_ownership or [])})
    if baseline_sha and not SHA.fullmatch(baseline_sha):raise OrchestrationError("Baseline must be a full Git SHA")
    with locked(root) as s:
        if tid in s["tasks"]:raise OrchestrationError("Task already exists")
        for d in deps:
            if d not in s["tasks"]:raise OrchestrationError(f"Dependency task {d} is missing")
        check_files(s,tid,files)
        t={"task_id":tid,"title":clean(title,"title"),"parent_task_id":parent_task_id,"participants":{"boss":boss_thread_id,"pm":pm_thread_id,"professional":professional_thread_id},"reviewer_thread_id":None,"role":role,"authorization":copy.deepcopy(authorization),"dependencies":deps,"phase":phase,"mode":mode,"status":"planned","branch":clean(branch),"worktree":clean(worktree),"baseline_sha":baseline_sha,"file_ownership":files,"ownership_released":False,"versions":copy.deepcopy(versions or {}),"freeze":None,"post_freeze_versions":[],"candidates":[],"current_candidate_id":None,"reviews":[],"cancellation":{"requested":False,"confirmed_stopped":False},"created_at":now(),"updated_at":now()}
        s["tasks"][tid]=t; audit(s,"task_created",actor,{"task_id":tid,"role":role,"mode":mode,"phase":phase}); return copy.deepcopy(t)
def transition(root,tid,action,actor=None):
    allowed={"accept-dependencies":{"planned"},"start":{"ready","returned","insufficient"},"rework":{"returned","insufficient"}}
    if action not in allowed:raise OrchestrationError("Unknown task transition")
    with locked(root) as s:
        t=task(s,tid)
        if t["status"] not in allowed[action]:raise OrchestrationError("Invalid task transition")
        if action=="accept-dependencies" and any(task(s,d)["status"]!="accepted" for d in t["dependencies"]):raise OrchestrationError("Dependencies have not been accepted")
        t["status"]="ready" if action=="accept-dependencies" else "running"; t["updated_at"]=now(); audit(s,"task_transition",actor,{"task_id":tid,"action":action}); return copy.deepcopy(t)
def freeze(root,tid,*,snapshot_id,as_of,cutoff,summary,actor=None,**versions):
    f={"snapshot_id":ident(snapshot_id,"snapshot ID"),"as_of":clean(as_of),"cutoff":clean(cutoff),"summary":clean(summary),**{k:clean(v) for k,v in versions.items()},"frozen_at":now()}
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
        t["post_freeze_versions"].append(v); audit(s,"post_freeze_version",actor,{"task_id":tid,"snapshot_id":snapshot_id}); return copy.deepcopy(v)
def deliver(root,tid,*,artifact,candidate_id=None,commit_sha="",snapshot_id="",new_version=False,evidence=None,actor=None):
    if commit_sha and not SHA.fullmatch(commit_sha):raise OrchestrationError("Candidate commit must be a full Git SHA")
    if not artifact:raise OrchestrationError("Candidate artifact is required")
    cid=ident(candidate_id,"candidate ID") if candidate_id else "cand-"+secrets.token_hex(8)
    with locked(root) as s:
        t=task(s,tid)
        if t["status"]!="running":raise OrchestrationError("Candidate delivery requires a running task")
        if any(x["candidate_id"]==cid for x in t["candidates"]):raise OrchestrationError("Candidate ID already exists")
        if t["freeze"] is not None:
            if not new_version and snapshot_id!=t["freeze"]["snapshot_id"]:raise OrchestrationError("Frozen task cannot be backfilled")
            if new_version and snapshot_id==t["freeze"]["snapshot_id"]:raise OrchestrationError("New candidate needs a new snapshot ID")
        c={"candidate_id":cid,"commit_sha":commit_sha,"artifact":clean(artifact),"snapshot_id":snapshot_id or None,"new_version":bool(new_version),"evidence":copy.deepcopy(evidence or {}),"status":"pending_review","delivered_at":now()}; t["candidates"].append(c); t["current_candidate_id"]=cid; t["status"]="delivered"; audit(s,"candidate_delivered",actor,{"task_id":tid,"candidate_id":cid}); return copy.deepcopy(c)
def review(root,tid,*,candidate_id,result,reviewer_thread_id,notes="",actor=None):
    if result not in {"passed","returned","insufficient"}:raise OrchestrationError("Invalid review result")
    reviewer_thread_id=real_thread(reviewer_thread_id,"review thread ID")
    with locked(root) as s:
        t=task(s,tid)
        if t["status"]!="delivered" or t["current_candidate_id"]!=candidate_id:raise OrchestrationError("Review must bind to current candidate")
        if reviewer_thread_id==t["participants"]["professional"]:raise OrchestrationError("Implementer cannot independently review")
        if t.get("reviewer_thread_id") and t["reviewer_thread_id"]!=reviewer_thread_id:raise OrchestrationError("Review must use the task's assigned independent reviewer")
        if not t.get("reviewer_thread_id"): t["reviewer_thread_id"]=reviewer_thread_id
        c=next((x for x in t["candidates"] if x["candidate_id"]==candidate_id),None)
        if not c or c["status"]!="pending_review":raise OrchestrationError("Candidate is not awaiting review")
        r={"candidate_id":candidate_id,"reviewer_thread_id":reviewer_thread_id,"result":result,"notes":clean(notes),"reviewed_at":now()}; c["status"]=result; t["reviews"].append(r); t["status"]="reviewed" if result=="passed" else result; audit(s,"candidate_reviewed",actor,{"task_id":tid,"candidate_id":candidate_id,"result":result}); return copy.deepcopy(r)
def accept(root,tid,*,candidate_id,actor=None):
    with locked(root) as s:
        t=task(s,tid); c=next((x for x in t["candidates"] if x["candidate_id"]==candidate_id),None)
        if t["status"]!="reviewed" or t["current_candidate_id"]!=candidate_id or not c or c["status"]!="passed":raise OrchestrationError("Only a passed current candidate can be accepted")
        t["status"]="accepted"; audit(s,"task_accepted",actor,{"task_id":tid,"candidate_id":candidate_id}); return copy.deepcopy(t)
def cancel(root,tid,*,reason,actor=None):
    with locked(root) as s:
        t=task(s,tid); t["cancellation"]={"requested":True,"confirmed_stopped":False,"reason":clean(reason),"requested_at":now()}; t["status"]="cancellation_requested"; audit(s,"cancellation_requested",actor,{"task_id":tid}); return copy.deepcopy(t)
def confirm_stop(root,tid,*,actor,evidence=""):
    with locked(root) as s:
        t=task(s,tid)
        if not t["cancellation"].get("requested"):raise OrchestrationError("Cancellation must be requested first")
        if actor!=t["participants"]["professional"] and not isinstance(evidence,dict):raise OrchestrationError("Stop confirmation requires the executor or recovery evidence")
        if isinstance(evidence,dict) and not evidence.get("recovery_verified"):raise OrchestrationError("Recovery evidence is not verified")
        t["cancellation"].update({"confirmed_stopped":True,"confirmed_at":now(),"evidence":clean(evidence)}); t["status"]="confirmed_stopped"; audit(s,"confirmed_stopped",actor,{"task_id":tid}); return copy.deepcopy(t)
def release_files(root,tid,*,actor):
    with locked(root) as s:
        t=task(s,tid)
        if t["status"] not in {"accepted","confirmed_stopped"}:raise OrchestrationError("Ownership remains until acceptance or confirmed stop")
        t["ownership_released"]=True; t["released_at"]=now(); audit(s,"file_ownership_released",actor,{"task_id":tid}); return copy.deepcopy(t)
def dispatch_register(root,*,dispatch_key,task_id,role,operation_id=None,client_thread_id=None,actor=None):
    if role not in roles(root):raise OrchestrationError("Unknown role ID")
    if not operation_id and not client_thread_id:raise OrchestrationError("Pending creation needs an operation or client ID")
    with locked(root) as s:
        task(s,task_id)
        if dispatch_key in s["dispatches"]:raise OrchestrationError("Dispatch key is already used or pending")
        r={"dispatch_key":ident(dispatch_key,"dispatch key"),"task_id":task_id,"role":role,"operation_id":operation_id,"client_thread_id":client_thread_id,"thread_id":None,"status":"pending_creation","created_at":now()}; s["dispatches"][dispatch_key]=r; audit(s,"dispatch_registered",actor,{"dispatch_key":dispatch_key}); return copy.deepcopy(r)
def dispatch_confirm(root,*,dispatch_key,thread_id,actor=None):
    thread_id=real_thread(thread_id)
    with locked(root) as s:
        try:r=s["dispatches"][dispatch_key]
        except KeyError as e:raise OrchestrationError("Dispatch key does not exist") from e
        if r["status"]=="confirmed":
            if r["thread_id"]!=thread_id:raise OrchestrationError("Dispatch already has another thread")
            return copy.deepcopy(r)
        if r.get("client_thread_id")==thread_id:raise OrchestrationError("Client ID cannot be used as thread ID")
        r.update({"thread_id":thread_id,"status":"confirmed","confirmed_at":now()}); audit(s,"dispatch_confirmed",actor,{"dispatch_key":dispatch_key}); return copy.deepcopy(r)
def remote_main(root,fetch=False):
    if fetch:git(root,"fetch","origin","main")
    sha=git(root,"rev-parse","origin/main")
    if not sha or not SHA.fullmatch(sha):raise OrchestrationError("origin/main is unavailable")
    v=git(root,"show",f"{sha}:VERSION")
    if not v or not SEMVER.fullmatch(v):raise OrchestrationError("origin/main VERSION is invalid")
    a,b,c=map(int,v.split(".")); return sha,v,f"{a}.{b}.{c+1}"
def acquire_lock(root,*,task_id,pm_thread_id,candidate_id,expected_version=None,fetch=False,actor=None):
    pm_thread_id=real_thread(pm_thread_id,"PM thread ID"); base,old,nxt=remote_main(root,fetch)
    if expected_version and expected_version!=nxt:raise OrchestrationError("Publish version is stale")
    with locked(root) as s:
        t=task(s,task_id)
        if t["participants"]["pm"]!=pm_thread_id:raise OrchestrationError("Publish PM does not match task PM")
        if t["status"]!="accepted" or t.get("current_candidate_id")!=candidate_id:raise OrchestrationError("Publish lock requires the accepted current candidate")
        candidate=next((c for c in t["candidates"] if c["candidate_id"]==candidate_id),None)
        if not candidate or candidate.get("status")!="passed":raise OrchestrationError("Publish lock requires independent review evidence")
        if t.get("baseline_sha") and git(root,"merge-base","--is-ancestor",t["baseline_sha"],base,optional=True) is None:raise OrchestrationError("Task baseline is outside latest origin/main history")
        if s.get("publish_lock"):raise OrchestrationError("Another PM holds publish lock; no timeout takeover")
        l={"task_id":task_id,"pm_thread_id":pm_thread_id,"candidate_id":candidate_id,"baseline_sha":t.get("baseline_sha"),"base_sha":base,"remote_version":old,"version":nxt,"coordination_version":nxt,"acquired_at":now()}; s["publish_lock"]=l; audit(s,"publish_lock_acquired",actor,{"task_id":task_id,"version":nxt,"candidate_id":candidate_id}); return copy.deepcopy(l)
def release_lock(root,*,task_id,pm_thread_id,actor=None):
    with locked(root) as s:
        l=s.get("publish_lock")
        if not l or l["task_id"]!=task_id or l["pm_thread_id"]!=pm_thread_id:raise OrchestrationError("Only lock owner may release")
        s["publish_lock"]=None; audit(s,"publish_lock_released",actor,{"task_id":task_id})
def recover_lock(root,*,task_id,pm_thread_id,coordinator_id,evidence,actor=None):
    required=("holder_status","remote_git","actions","tag","release","notification")
    if not isinstance(evidence,dict) or any(k not in evidence or evidence[k] in (None,"","unknown","ambiguous","pending") for k in required):raise OrchestrationError("Recovery evidence is incomplete or ambiguous")
    with locked(root) as s:
        l=s.get("publish_lock")
        if not l or l["task_id"]!=task_id or l["pm_thread_id"]!=pm_thread_id:raise OrchestrationError("Recovery target does not match lock")
        s["publish_lock"]=None; audit(s,"publish_lock_recovered",actor or coordinator_id,{"task_id":task_id,"coordinator_id":coordinator_id,"evidence":copy.deepcopy(evidence)})

def main(argv=None,root=None):
    root=Path(root or Path(__file__).resolve().parents[4]); p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="c",required=True); sub.add_parser("show")
    x=sub.add_parser("task-create");
    for n in ("task-id","title","boss","pm","professional","role","mode","authorization"):x.add_argument("--"+n,required=True)
    x.add_argument("--phase",type=int,required=True); x.add_argument("--dependencies",default="[]"); x.add_argument("--files",default="[]")
    x=sub.add_parser("task-transition");x.add_argument("task_id");x.add_argument("action")
    x=sub.add_parser("dispatch-register");x.add_argument("--dispatch-key",required=True);x.add_argument("--task-id",required=True);x.add_argument("--role",required=True);x.add_argument("--client-thread-id");x.add_argument("--operation-id")
    x=sub.add_parser("dispatch-confirm");x.add_argument("--dispatch-key",required=True);x.add_argument("--thread-id",required=True)
    x=sub.add_parser("publish-lock-acquire");x.add_argument("--task-id",required=True);x.add_argument("--pm",required=True);x.add_argument("--candidate-id",required=True);x.add_argument("--expected-version");x.add_argument("--no-fetch",action="store_true")
    x=sub.add_parser("publish-lock-release");x.add_argument("--task-id",required=True);x.add_argument("--pm",required=True)
    a=p.parse_args(argv)
    try:
        if a.c=="show":r=read_state(root)
        elif a.c=="task-create":r=create_task(root,task_id=a.task_id,title=a.title,parent_task_id=None,boss_thread_id=a.boss,pm_thread_id=a.pm,professional_thread_id=a.professional,role=a.role,phase=a.phase,mode=a.mode,authorization=json.loads(a.authorization),dependencies=json.loads(a.dependencies),file_ownership=json.loads(a.files))
        elif a.c=="task-transition":r=transition(root,a.task_id,a.action)
        elif a.c=="dispatch-register":r=dispatch_register(root,dispatch_key=a.dispatch_key,task_id=a.task_id,role=a.role,client_thread_id=a.client_thread_id,operation_id=a.operation_id)
        elif a.c=="dispatch-confirm":r=dispatch_confirm(root,dispatch_key=a.dispatch_key,thread_id=a.thread_id)
        elif a.c=="publish-lock-acquire":r=acquire_lock(root,task_id=a.task_id,pm_thread_id=a.pm,candidate_id=a.candidate_id,expected_version=a.expected_version,fetch=not a.no_fetch)
        else:r=release_lock(root,task_id=a.task_id,pm_thread_id=a.pm) or {"released":True}
        print(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)); return 0
    except (OrchestrationError,ValueError,TypeError) as e: print(f"Orchestration failed: {e}",file=sys.stderr); return 1
if __name__=="__main__":raise SystemExit(main())
