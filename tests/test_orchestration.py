import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

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

if __name__=="__main__": unittest.main()
