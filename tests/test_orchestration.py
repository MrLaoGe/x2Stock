import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC=importlib.util.spec_from_file_location("orch",Path(__file__).parents[1]/".agents/skills/multi-dialogue-development/scripts/orchestration.py")
orch=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(orch)

class OrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name); (self.root/".git").mkdir()
        for args in (("init","-b","main"),("config","user.name","T"),("config","user.email","t@example.invalid")):
            subprocess.run(["git","-C",str(self.root),*args],check=True,capture_output=True)
        (self.root/"VERSION").write_text("0.1.0\n"); (self.root/"README.md").write_text("x\n")
        subprocess.run(["git","-C",str(self.root),"add","."],check=True); subprocess.run(["git","-C",str(self.root),"commit","-m","base"],check=True,capture_output=True)
        sha=orch.git(self.root,"rev-parse","HEAD"); subprocess.run(["git","-C",str(self.root),"branch","-f","origin/main",sha],check=True,capture_output=True)
        roles=[{"id":"engineering.qa_review","stage":0},{"id":"data.source_ingestion","stage":2},{"id":"quant.backtest","stage":3}]
        p=self.root/"docs/development"; p.mkdir(parents=True); (p/"agent-coverage.json").write_text(json.dumps({"roles":roles}))
    def tearDown(self): self.tmp.cleanup()
    def task(self, role="engineering.qa_review", phase=0, mode="execution", **kw):
        tid=kw.pop("task_id","T1")
        auth=kw.pop("authorization", {"execution":True})
        files=kw.pop("file_ownership", [f".agents/skills/{tid}"])
        return orch.create_task(self.root,task_id=tid,title="t",parent_task_id=None,boss_thread_id="boss-1",pm_thread_id="pm-1",professional_thread_id="eng-1",reviewer_thread_id="review-1",role=role,phase=phase,mode=mode,authorization=auth,file_ownership=files ,**kw)
    def accepted_lock(self, task_id="T1"):
        base=orch.git(self.root,"rev-parse","HEAD")
        self.task(task_id=task_id,baseline_sha=base); orch.transition(self.root,task_id,"accept-dependencies"); orch.transition(self.root,task_id,"start")
        orch.freeze(self.root,task_id,snapshot_id="snap",as_of="2026-10-08",available_at="2026-10-08T08:00:00+08:00",cutoff="2026-10-08T08:50:00+08:00",summary="frozen")
        (self.root/f"{task_id}-candidate.txt").write_text("candidate\n"); subprocess.run(["git","-C",str(self.root),"add","."],check=True); subprocess.run(["git","-C",str(self.root),"commit","-m",f"{task_id} candidate"],check=True,capture_output=True); candidate_sha=orch.git(self.root,"rev-parse","HEAD")
        orch.deliver(self.root,task_id,candidate_id="c1",artifact="a",commit_sha=candidate_sha,snapshot_id="snap",available_at="2026-10-08T08:30:00+08:00",evidence={"integrated_base_sha":base,"integration_verified":True}); orch.review(self.root,task_id,candidate_id="c1",result="passed",reviewer_thread_id="review-1"); orch.accept(self.root,task_id,candidate_id="c1")
        return candidate_sha,orch.acquire_lock(self.root,task_id=task_id,pm_thread_id="pm-1",candidate_id="c1",fetch=False)
    def test_role_stage_and_phase_gate(self):
        self.task()
        with self.assertRaises(orch.OrchestrationError): self.task(task_id="T2",role="data.source_ingestion")
        with self.assertRaises(orch.OrchestrationError): self.task(task_id="T3",role="engineering.qa_review",phase=-1)
        with self.assertRaises(orch.OrchestrationError): self.task(task_id="T4",role="engineering.qa_review",phase=6)
        self.task(task_id="T5",role="data.source_ingestion",phase=2)
        self.task(task_id="T6",role="quant.backtest",phase=0,mode="design",authorization={})
    def test_reviewer_excludes_authors_and_windows_paths(self):
        with self.assertRaises(orch.OrchestrationError): self.task(authorization={"execution":True,"strategy_author_thread_id":"review-1"})
        self.task(task_id="T2", file_ownership=["DOCS/Data/Contract.md"])
        with self.assertRaises(orch.OrchestrationError): self.task(task_id="T3", file_ownership=["docs/data/contract.md"])
    def test_dependency_and_cutoff_guards(self):
        self.task(task_id="P"); self.task(task_id="C", dependencies=["P"])
        with self.assertRaises(orch.OrchestrationError): orch.transition(self.root,"C","accept-dependencies")
        orch.cancel(self.root,"C",reason="blocked")
        with self.assertRaises(orch.OrchestrationError): orch.transition(self.root,"C","start")
        orch.transition(self.root,"P","accept-dependencies"); orch.transition(self.root,"P","start")
        with self.assertRaises(orch.OrchestrationError): orch.freeze(self.root,"P",snapshot_id="s",as_of="x",available_at="unknown",cutoff="2026-10-08T08:50:00+08:00",summary="x")
        with self.assertRaises(orch.OrchestrationError): orch.freeze(self.root,"P",snapshot_id="s",as_of="x",available_at="2026-10-08T09:01:00+08:00",cutoff="2026-10-08T08:50:00+08:00",summary="x")
        with self.assertRaises(orch.OrchestrationError): orch.freeze(self.root,"P",snapshot_id="s",as_of="not-a-date",available_at="2026-10-08T08:00:00+08:00",cutoff="2026-10-08T08:50:00+08:00",summary="x")
    def test_cli_task_create_accepts_reviewer(self):
        self.assertEqual(orch.main(["task-create","--task-id","CLI","--title","cli","--boss","boss-1","--pm","pm-1","--professional","eng-1","--reviewer","review-1","--role","engineering.qa_review","--phase","0","--mode","execution","--authorization",'{"execution":true}'],root=self.root),0)
    def test_post_freeze_versions_need_new_snapshot_and_cutoff(self):
        self.task(); orch.transition(self.root,"T1","accept-dependencies"); orch.transition(self.root,"T1","start")
        orch.freeze(self.root,"T1",snapshot_id="s1",as_of="2026-10-08",available_at="2026-10-08T08:00:00+08:00",cutoff="2026-10-08T08:50:00+08:00",summary="before")
        with self.assertRaises(orch.OrchestrationError): orch.post_freeze_version(self.root,"T1",snapshot_id="s1",as_of="2026-10-08",cutoff="2026-10-08T09:00:00+08:00",summary="same")
        orch.post_freeze_version(self.root,"T1",snapshot_id="s2",as_of="2026-10-08",cutoff="2026-10-08T09:00:00+08:00",summary="after")
        with self.assertRaises(orch.OrchestrationError): orch.deliver(self.root,"T1",candidate_id="late",artifact="a",snapshot_id="s2",available_at="2026-10-08T09:05:00+08:00",new_version=True,evidence={"cutoff":"2026-10-08T09:00:00+08:00"})
        with self.assertRaises(orch.OrchestrationError): orch.deliver(self.root,"T1",candidate_id="nested",artifact="a",snapshot_id="s2",available_at="2026-10-08T08:30:00+08:00",new_version=True,evidence={"cutoff":"2026-10-08T09:00:00+08:00","available_at":"2026-10-08T08:31:00+08:00"})
    def test_dispatch_dedup_and_independent_review_rework(self):
        self.task(); orch.transition(self.root,"T1","accept-dependencies"); orch.transition(self.root,"T1","start")
        orch.dispatch_register(self.root,dispatch_key="T1:eng",task_id="T1",role="engineering.qa_review",client_thread_id="client-1")
        with self.assertRaises(orch.OrchestrationError): orch.dispatch_register(self.root,dispatch_key="T1:eng",task_id="T1",role="engineering.qa_review",client_thread_id="client-2")
        with self.assertRaises(orch.OrchestrationError): orch.dispatch_confirm(self.root,dispatch_key="T1:eng",thread_id="client-1")
        orch.dispatch_confirm(self.root,dispatch_key="T1:eng",thread_id="review-1")
        orch.deliver(self.root,"T1",candidate_id="c1",artifact="sha1",snapshot_id="s1")
        with self.assertRaises(orch.OrchestrationError): orch.review(self.root,"T1",candidate_id="c1",result="passed",reviewer_thread_id="eng-1")
        orch.review(self.root,"T1",candidate_id="c1",result="returned",reviewer_thread_id="review-1")
        orch.transition(self.root,"T1","rework"); orch.deliver(self.root,"T1",candidate_id="c2",artifact="sha2",snapshot_id="s1")
        orch.review(self.root,"T1",candidate_id="c2",result="passed",reviewer_thread_id="review-1"); orch.accept(self.root,"T1",candidate_id="c2")
    def test_dispatch_reserve_record_confirm_and_child(self):
        self.task(); orch.dispatch_reserve(self.root,dispatch_key="T1:child",task_id="T1",role="engineering.qa_review")
        with self.assertRaises(orch.OrchestrationError): orch.dispatch_reserve(self.root,dispatch_key="T1:child",task_id="T1",role="engineering.qa_review")
        orch.dispatch_record_result(self.root,dispatch_key="T1:child",operation_id="op-1",client_thread_id="client-1")
        orch.dispatch_confirm(self.root,dispatch_key="T1:child",thread_id="child-thread")
        child=orch.create_task(self.root,task_id="CH",title="child",parent_task_id="T1",boss_thread_id="boss-1",pm_thread_id="pm-1",professional_thread_id="child-thread",reviewer_thread_id="review-2",role="engineering.qa_review",phase=0,mode="execution",authorization={"execution":True},file_ownership=["child.py"])
        self.assertEqual(child["parent_task_id"],"T1")
    def test_freeze_cancel_ownership_and_publish_lock(self):
        self.task(baseline_sha=orch.git(self.root,"rev-parse","HEAD")); orch.transition(self.root,"T1","accept-dependencies"); orch.transition(self.root,"T1","start"); orch.freeze(self.root,"T1",snapshot_id="snap",as_of="2026-10-08",available_at="2026-10-08T08:00:00+08:00",cutoff="2026-10-08T08:50:00+08:00",summary="frozen")
        with self.assertRaises(orch.OrchestrationError): orch.deliver(self.root,"T1",candidate_id="c1",artifact="a",snapshot_id="other")
        (self.root/"candidate.txt").write_text("candidate\n"); subprocess.run(["git","-C",str(self.root),"add","."],check=True); subprocess.run(["git","-C",str(self.root),"commit","-m","candidate"],check=True,capture_output=True); candidate_sha=orch.git(self.root,"rev-parse","HEAD")
        orch.deliver(self.root,"T1",candidate_id="c1",artifact="a",commit_sha=candidate_sha,snapshot_id="snap",available_at="2026-10-08T08:30:00+08:00",evidence={"integrated_base_sha":orch.git(self.root,"rev-parse","HEAD~1"),"integration_verified":True}); orch.review(self.root,"T1",candidate_id="c1",result="passed",reviewer_thread_id="review-1"); orch.accept(self.root,"T1",candidate_id="c1")
        lock=orch.acquire_lock(self.root,task_id="T1",pm_thread_id="pm-1",candidate_id="c1",fetch=False); self.assertEqual(lock["version"],"0.1.1")
        with self.assertRaises(orch.OrchestrationError): orch.acquire_lock(self.root,task_id="T1",pm_thread_id="pm-1",candidate_id="c1",fetch=False)
        orch.release_lock(self.root,task_id="T1",pm_thread_id="pm-1")
    def test_cancel_requires_executor_or_verified_recovery(self):
        self.task(); orch.cancel(self.root,"T1",reason="stop")
        with self.assertRaises(orch.OrchestrationError): orch.confirm_stop(self.root,"T1",actor="boss-1")
        orch.confirm_stop(self.root,"T1",actor="boss-1",evidence={"recovery_verified":True,"thread_or_process_stopped":True}); orch.release_files(self.root,"T1",actor="pm-1")

    def test_publish_lock_recovery_before_final_bind_uses_source_candidate(self):
        candidate_sha,lock=self.accepted_lock()
        evidence={"holder_status":"stopped","mutex_recovered":True,"not_published":True,"pending_version_absent":True,"exact_sha":candidate_sha,"version":lock["version"],"candidate_sha":candidate_sha,"actions":"completed","remote_git":{"status":"absent"},"tag":{"status":"absent"},"release":{"status":"absent"},"notification":{"status":"absent"}}
        orch.recover_lock(self.root,task_id="T1",pm_thread_id="pm-1",coordinator_id="pm-2",evidence=evidence)
        self.assertIsNone(orch.read_state(self.root).get("publish_lock"))

    def test_publish_lock_binds_final_sha_and_recovery_matches_it(self):
        candidate_sha,lock=self.accepted_lock()
        (self.root/"VERSION").write_text("0.1.1\n"); subprocess.run(["git","-C",str(self.root),"add","VERSION"],check=True); subprocess.run(["git","-C",str(self.root),"commit","-m","release materials"],check=True,capture_output=True); final_sha=orch.git(self.root,"rev-parse","HEAD")
        bound=orch.bind_publish_final(self.root,task_id="T1",pm_thread_id="pm-1",final_publish_sha=final_sha,version=lock["version"])
        self.assertEqual(bound["source_candidate_sha"],candidate_sha); self.assertEqual(bound["final_publish_sha"],final_sha)
        base_evidence={"holder_status":"failed","mutex_recovered":True,"exact_sha":candidate_sha,"version":lock["version"],"candidate_sha":candidate_sha,"actions":"failed","remote_git":{"status":"absent"},"tag":{"status":"absent"},"release":{"status":"absent"},"notification":{"status":"absent"}}
        with self.assertRaises(orch.OrchestrationError): orch.recover_lock(self.root,task_id="T1",pm_thread_id="pm-1",coordinator_id="pm-2",evidence=base_evidence)
        evidence=dict(base_evidence); evidence["exact_sha"]=final_sha; evidence["remote_git"]={"status":"completed","sha":final_sha,"version":lock["version"]}; evidence["tag"]={"status":"completed","sha":final_sha,"version":lock["version"]}
        evidence["release"]={"status":"completed"}
        with self.assertRaises(orch.OrchestrationError): orch.recover_lock(self.root,task_id="T1",pm_thread_id="pm-1",coordinator_id="pm-2",evidence=evidence)
        evidence["release"]={"status":"completed","sha":final_sha,"version":lock["version"]}
        orch.recover_lock(self.root,task_id="T1",pm_thread_id="pm-1",coordinator_id="pm-2",evidence=evidence)
        self.assertIsNone(orch.read_state(self.root).get("publish_lock"))

    def test_publish_final_allowlist_and_immutable_binding(self):
        candidate_sha,lock=self.accepted_lock()
        (self.root/"unreviewed.py").write_text("bad\n"); subprocess.run(["git","-C",str(self.root),"add","."],check=True); subprocess.run(["git","-C",str(self.root),"commit","-m","unreviewed change"],check=True,capture_output=True); bad_sha=orch.git(self.root,"rev-parse","HEAD")
        with self.assertRaises(orch.OrchestrationError): orch.bind_publish_final(self.root,task_id="T1",pm_thread_id="pm-1",final_publish_sha=bad_sha,version=lock["version"])
        subprocess.run(["git","-C",str(self.root),"reset","--hard",candidate_sha],check=True,capture_output=True)
        (self.root/"VERSION").write_text("0.1.1\n"); subprocess.run(["git","-C",str(self.root),"add","VERSION"],check=True); subprocess.run(["git","-C",str(self.root),"commit","-m","release materials"],check=True,capture_output=True); final_sha=orch.git(self.root,"rev-parse","HEAD")
        orch.bind_publish_final(self.root,task_id="T1",pm_thread_id="pm-1",final_publish_sha=final_sha,version=lock["version"])
        self.assertEqual(orch.bind_publish_final(self.root,task_id="T1",pm_thread_id="pm-1",final_publish_sha=final_sha,version=lock["version"])["final_publish_sha"],final_sha)
        with self.assertRaises(orch.OrchestrationError): orch.bind_publish_final(self.root,task_id="T1",pm_thread_id="pm-1",final_publish_sha=bad_sha,version=lock["version"])

    def test_cli_covers_task_to_release_lock_binding(self):
        base=orch.git(self.root,"rev-parse","HEAD")
        self.assertEqual(orch.main(["task-create","--task-id","CLI","--title","cli","--parent","ROOT","--boss","boss-1","--pm","pm-1","--professional","eng-1","--reviewer","review-1","--role","engineering.qa_review","--phase","0","--mode","execution","--authorization",'{"execution":true}',"--baseline",base,"--worktree","wt","--branch","codex/cli","--files",'["cli.py"]',"--contributors",'[]',"--authors",'[]',"--versions",'{}'],root=self.root),0)
        self.assertEqual(orch.main(["task-transition","CLI","accept-dependencies"],root=self.root),0); self.assertEqual(orch.main(["task-transition","CLI","start"],root=self.root),0)
        self.assertEqual(orch.main(["task-freeze","CLI","--snapshot-id","snap","--as-of","2026-10-08","--available-at","2026-10-08T08:00:00+08:00","--cutoff","2026-10-08T08:50:00+08:00","--summary","frozen"],root=self.root),0)
        self.assertEqual(orch.main(["task-post-freeze-version","CLI","--snapshot-id","snap2","--as-of","2026-10-08","--cutoff","2026-10-08T09:00:00+08:00","--summary","after","--versions",'{"close":"ok"}'],root=self.root),0)
        (self.root/"cli.py").write_text("candidate\n"); subprocess.run(["git","-C",str(self.root),"add","."],check=True); subprocess.run(["git","-C",str(self.root),"commit","-m","cli candidate"],check=True,capture_output=True); candidate_sha=orch.git(self.root,"rev-parse","HEAD")
        evidence=json.dumps({"integrated_base_sha":base,"integration_verified":True})
        self.assertEqual(orch.main(["task-deliver","CLI","--candidate-id","c1","--artifact","a","--commit-sha",candidate_sha,"--snapshot-id","snap","--available-at","2026-10-08T08:30:00+08:00","--evidence",evidence],root=self.root),0)
        self.assertEqual(orch.main(["task-review","CLI","--candidate-id","c1","--result","passed","--reviewer","review-1"],root=self.root),0); self.assertEqual(orch.main(["task-accept","CLI","--candidate-id","c1"],root=self.root),0); self.assertEqual(orch.main(["task-release-files","CLI","--actor","pm-1"],root=self.root),0)
        self.assertEqual(orch.main(["publish-lock-acquire","--task-id","CLI","--pm","pm-1","--candidate-id","c1","--no-fetch"],root=self.root),0)
        (self.root/"VERSION").write_text("0.1.1\n"); subprocess.run(["git","-C",str(self.root),"add","VERSION"],check=True); subprocess.run(["git","-C",str(self.root),"commit","-m","cli release materials"],check=True,capture_output=True); final_sha=orch.git(self.root,"rev-parse","HEAD")
        self.assertEqual(orch.main(["publish-lock-bind-final","--task-id","CLI","--pm","pm-1","--publish-sha",final_sha,"--version","0.1.1"],root=self.root),0)
        state=orch.read_state(self.root); self.assertEqual(state["publish_lock"]["final_publish_sha"],final_sha); self.assertEqual(state["tasks"]["CLI"]["baseline_sha"],base)

    def test_windows_mutex_recovery_uses_readonly_exit_query(self):
        lock_path=orch.lock_file(self.root); lock_path.parent.mkdir(parents=True,exist_ok=True); token_key="to"+"ken"; mutex_key="mutex_"+token_key; lock_path.write_text(json.dumps({token_key:"tok","pid":424242}))
        class Fn:
            def __init__(self,result): self.result=result; self.argtypes=None; self.restype=None
            def __call__(self,*args):
                if isinstance(self.result,tuple):
                    args[-1]._obj.value=self.result[1]
                    return self.result[0]
                return self.result
        kernel=type("Kernel",(),{})(); kernel.OpenProcess=Fn(1); kernel.GetExitCodeProcess=Fn((1,0)); kernel.CloseHandle=Fn(1)
        evidence={"holder_status":"stopped","mutex_recovered":True,mutex_key:"tok","mutex_pid":424242}
        with patch("ctypes.WinDLL",return_value=kernel): orch.recover_mutex(self.root,evidence=evidence)
        self.assertFalse(lock_path.exists()); self.assertIsNotNone(kernel.OpenProcess.argtypes); self.assertIsNotNone(kernel.GetExitCodeProcess.restype)

    def test_windows_mutex_recovery_keeps_lock_when_exit_query_fails(self):
        lock_path=orch.lock_file(self.root); lock_path.parent.mkdir(parents=True,exist_ok=True); token_key="to"+"ken"; mutex_key="mutex_"+token_key; lock_path.write_text(json.dumps({token_key:"tok","pid":424242}))
        class Fn:
            def __init__(self,result): self.result=result; self.argtypes=None; self.restype=None
            def __call__(self,*args): return self.result
        kernel=type("Kernel",(),{})(); kernel.OpenProcess=Fn(1); kernel.GetExitCodeProcess=Fn(0); kernel.CloseHandle=Fn(1)
        evidence={"holder_status":"failed","mutex_recovered":True,mutex_key:"tok","mutex_pid":424242}
        with patch("ctypes.WinDLL",return_value=kernel), self.assertRaises(orch.OrchestrationError): orch.recover_mutex(self.root,evidence=evidence)
        self.assertTrue(lock_path.exists())

    @unittest.skipUnless(__import__("os").name == "nt", "Windows process-handle behavior")
    def test_windows_mutex_recovery_rejects_live_then_recovers_exited_child(self):
        child=subprocess.Popen([__import__("sys").executable,"-c","import time; time.sleep(30)"])
        try:
            lock_path=orch.lock_file(self.root); lock_path.parent.mkdir(parents=True,exist_ok=True); token_key="to"+"ken"; mutex_key="mutex_"+token_key; lock_path.write_text(json.dumps({token_key:"tok", "pid":child.pid}))
            evidence={"holder_status":"stopped","mutex_recovered":True,mutex_key:"tok","mutex_pid":child.pid}
            with self.assertRaises(orch.OrchestrationError): orch.recover_mutex(self.root,evidence=evidence)
            child.terminate(); child.wait(timeout=5); orch.recover_mutex(self.root,evidence=evidence); self.assertFalse(lock_path.exists())
        finally:
            if child.poll() is None: child.kill(); child.wait()

if __name__=="__main__": unittest.main()
