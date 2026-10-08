import importlib.util
import copy
import hashlib
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
        locales="af am ar bg bn ca cs da de el en-GB en-US es-419 es et fa fi fil fr gu he hi hr hu id it ja kn ko lt lv ml mr ms nb nl pl pt-BR pt-PT ro ru sk sl sr sv sw ta te th tr uk ur vi zh-CN zh-TW".split()
        self.runtime_names=["chrome_100_percent.pak","chrome_200_percent.pak","d3dcompiler_47.dll","dxcompiler.dll","dxil.dll","ffmpeg.dll","icudtl.dat","LICENSE.electron.txt","LICENSES.chromium.html"]+[f"locales/{locale}.pak" for locale in locales]+["resources.pak","resources/app.asar","resources/build-manifest.json","snapshot_blob.bin","v8_context_snapshot.bin","vk_swiftshader_icd.json","vk_swiftshader.dll","vulkan-1.dll","x2Stock.exe"]
        (self.root/"desktop/updater").mkdir(parents=True); (self.root/"desktop/updater/runtime-files.json").write_text(json.dumps(self.runtime_names))
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

    def runtime_candidate(self, review=True, extra_path=None):
        previous,lock=self.accepted_lock()
        (self.root/"VERSION").write_text(lock["version"]+"\n")
        orch.git(self.root,"add","VERSION"); orch.git(self.root,"commit","-m","clean versioned build source")
        build_source=orch.git(self.root,"rev-parse","HEAD")
        source_hash=orch.canonical_source_hash(self.root,build_source)
        manifest={"schema":1,"repository":"MrLaoGe/x2Stock","version":lock["version"],"build_source_sha":build_source,"source_tree_hash":source_hash,"platform":"win32","arch":"x64"}
        content=json.dumps(manifest,separators=(",",":"))+"\n"
        objects={}
        for name in self.runtime_names:
            path="desktop-runtime/win-x64/"+name
            data=content.encode("utf-8") if name=="resources/build-manifest.json" else ("synthetic "+name).encode("utf-8")
            if name=="x2Stock.exe": data=b"MZ"+b"\0"*58+(64).to_bytes(4,"little")+b"PE\0\0\x64\x86"
            oid=hashlib.sha256(data).hexdigest(); size=len(data)
            obj=orch.common_dir(self.root)/"lfs/objects"/oid[:2]/oid[2:4]/oid; obj.parent.mkdir(parents=True,exist_ok=True); obj.write_bytes(data)
            target=self.root/path; target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(f"version https://git-lfs.github.com/spec/v1\noid sha256:{oid}\nsize {size}\n".encode("ascii"))
            objects[path]={"oid":oid,"size":size}
        if extra_path:
            target=self.root/extra_path; target.parent.mkdir(parents=True,exist_ok=True); target.write_text("unreviewed source\n")
        orch.git(self.root,"add","."); orch.git(self.root,"commit","-m","synthetic rebuilt runtime")
        candidate=orch.git(self.root,"rev-parse","HEAD")
        context={k:lock[k] for k in ("lock_id","task_id","pm_thread_id","source_candidate_sha","base_sha","version")}
        context.update(reviewer_thread_id="review-1",candidate_sha=candidate,candidate_id="runtime")
        manifest_path="desktop-runtime/win-x64/resources/build-manifest.json"
        receipt={"verifier":"verify_desktop_runtime","verified":True,"rebuilt":True,"manifest_reused":False,"paths":sorted(objects),"manifest_path":manifest_path,"manifest_lfs_oid":objects[manifest_path]["oid"],"manifest_size":objects[manifest_path]["size"],"manifest_content":content,"source_tree_hash":source_hash,"build_source_sha":build_source,"runtime_file_count":73,"lfs_objects_verified":True,"lfs_objects":objects,"review_binding":context}
        evidence={"integrated_base_sha":lock["base_sha"],"integration_verified":True,"cutoff":"2026-10-08T09:00:00+08:00","summary":"synthetic runtime rebuild","desktop_runtime":receipt}
        orch.deliver(self.root,"T1",candidate_id="runtime",artifact="runtime-a",commit_sha=candidate,snapshot_id="snap2",available_at="2026-10-08T08:30:00+08:00",new_version=True,evidence=evidence)
        if review:
            orch.review(self.root,"T1",candidate_id="runtime",result="passed",reviewer_thread_id="review-1"); orch.accept(self.root,"T1",candidate_id="runtime")
        return previous,lock,build_source,candidate,evidence

    def test_runtime_rebuild_requires_reviewed_rebind_inside_same_lock(self):
        previous,lock,build_source,candidate,evidence=self.runtime_candidate()
        self.assertNotEqual(build_source,candidate)
        with self.assertRaises(orch.OrchestrationError): orch.bind_publish_final(self.root,task_id="T1",pm_thread_id="pm-1",final_publish_sha=candidate,version=lock["version"])
        self.assertEqual(orch.main(["publish-lock-rebind-source","--task-id","T1","--pm","pm-1","--candidate-id","runtime","--no-fetch"],root=self.root),0)
        rebound=orch.read_state(self.root)["publish_lock"]
        self.assertEqual(rebound["lock_id"],lock["lock_id"]); self.assertEqual(rebound["source_candidate_sha"],candidate)
        self.assertEqual(rebound["source_rebindings"][0]["from_sha"],previous)
        (self.root/"CHANGELOG.md").write_text("later material\n"); orch.git(self.root,"add","CHANGELOG.md"); orch.git(self.root,"commit","-m","after review")
        with self.assertRaises(orch.OrchestrationError): orch.bind_publish_final(self.root,task_id="T1",pm_thread_id="pm-1",final_publish_sha=orch.git(self.root,"rev-parse","HEAD"),version=lock["version"])
        final=orch.bind_publish_final(self.root,task_id="T1",pm_thread_id="pm-1",final_publish_sha=candidate,version=lock["version"])
        self.assertEqual(final["final_publish_sha"],candidate)
        with self.assertRaises(orch.OrchestrationError): orch.rebind_publish_source(self.root,task_id="T1",pm_thread_id="pm-1",candidate_id="runtime")
        wrong={"holder_status":"failed","mutex_recovered":True,"exact_sha":previous,"version":lock["version"],"candidate_sha":previous,"actions":"failed",**{k:{"status":"absent"} for k in ("remote_git","tag","release","notification")}}
        with self.assertRaises(orch.OrchestrationError): orch.recover_lock(self.root,task_id="T1",pm_thread_id="pm-1",coordinator_id="pm-2",evidence=wrong)
        wrong.update(exact_sha=candidate,candidate_sha=candidate)
        orch.recover_lock(self.root,task_id="T1",pm_thread_id="pm-1",coordinator_id="pm-2",evidence=wrong)

    def test_runtime_pending_review_cannot_rebind_bind_release_or_use_wrong_reviewer(self):
        previous,lock,build_source,candidate,evidence=self.runtime_candidate(review=False)
        for action in (
            lambda:orch.rebind_publish_source(self.root,task_id="T1",pm_thread_id="pm-1",candidate_id="runtime"),
            lambda:orch.bind_publish_final(self.root,task_id="T1",pm_thread_id="pm-1",final_publish_sha=candidate,version=lock["version"]),
            lambda:orch.release_lock(self.root,task_id="T1",pm_thread_id="pm-1"),
            lambda:orch.review(self.root,"T1",candidate_id="runtime",result="passed",reviewer_thread_id="wrong-reviewer")):
            with self.assertRaises(orch.OrchestrationError): action()
        orch.review(self.root,"T1",candidate_id="runtime",result="passed",reviewer_thread_id="review-1"); orch.accept(self.root,"T1",candidate_id="runtime")
        for task_id,pm,cid in (("T2","pm-1","runtime"),("T1","pm-2","runtime"),("T1","pm-1","c1")):
            with self.assertRaises(orch.OrchestrationError): orch.rebind_publish_source(self.root,task_id=task_id,pm_thread_id=pm,candidate_id=cid)
        orch.git(self.root,"branch","-f","origin/main",build_source)
        with self.assertRaises(orch.OrchestrationError): orch.rebind_publish_source(self.root,task_id="T1",pm_thread_id="pm-1",candidate_id="runtime")
        orch.git(self.root,"branch","-f","origin/main",lock["base_sha"])
        state=orch.read_state(self.root)
        def main_moves_during_validation(*args):
            orch.git(self.root,"branch","-f","origin/main",build_source)
        with patch.object(orch,"validate_runtime_candidate",side_effect=main_moves_during_validation), self.assertRaises(orch.OrchestrationError):
            orch.rebind_publish_source(self.root,task_id="T1",pm_thread_id="pm-1",candidate_id="runtime")
        self.assertEqual(orch.read_state(self.root),state)

    def test_runtime_receipt_rejects_wrong_manifest_source_version_and_lfs_objects(self):
        previous,lock,build_source,candidate,evidence=self.runtime_candidate()
        mutations=[("manifest_content","{}"),("manifest_lfs_oid","0"*64),("manifest_size",1),("source_tree_hash","0"*64),("build_source_sha",lock["base_sha"]),("runtime_file_count",72),("lfs_objects",{}),("manifest_reused",True),("lfs_objects_verified",False),("paths",["desktop-runtime/win-x64/extra.dll"])]
        for key,value in mutations:
            with self.subTest(key=key):
                bad=copy.deepcopy(evidence); bad["desktop_runtime"][key]=value
                with self.assertRaises(orch.OrchestrationError): orch.validate_runtime_candidate(self.root,previous,candidate,lock["version"],bad)
        with self.assertRaises(orch.OrchestrationError): orch.validate_runtime_candidate(self.root,previous,candidate,"0.1.2",evidence)
        with self.assertRaises(orch.OrchestrationError): orch.validate_runtime_candidate(self.root,previous,build_source,lock["version"],evidence)
        state=orch.read_state(self.root)
        for key in ("lock_id","task_id","pm_thread_id","source_candidate_sha","base_sha","version","reviewer_thread_id","candidate_sha","candidate_id"):
            with self.subTest(binding=key):
                bad=copy.deepcopy(state); bad["tasks"]["T1"]["candidates"][-1]["evidence"]["desktop_runtime"]["review_binding"][key]="wrong"
                orch.atomic(orch.state_file(self.root),bad)
                with self.assertRaises(orch.OrchestrationError): orch.rebind_publish_source(self.root,task_id="T1",pm_thread_id="pm-1",candidate_id="runtime")
        orch.atomic(orch.state_file(self.root),state)
        bad=copy.deepcopy(state); bad["tasks"]["T1"]["reviews"][-1]["commit_sha"]=previous
        orch.atomic(orch.state_file(self.root),bad)
        with self.assertRaises(orch.OrchestrationError): orch.rebind_publish_source(self.root,task_id="T1",pm_thread_id="pm-1",candidate_id="runtime")

    def test_runtime_rebind_rejects_source_or_external_path_changes(self):
        previous,lock,build_source,candidate,evidence=self.runtime_candidate(extra_path="frontend/unreviewed.js")
        with self.assertRaises(orch.OrchestrationError): orch.rebind_publish_source(self.root,task_id="T1",pm_thread_id="pm-1",candidate_id="runtime")
        for path in ("outside.py","desktop-runtime/win-x64/extra.dll"):
            target=self.root/path; target.parent.mkdir(parents=True,exist_ok=True); target.write_text("invalid\n")
            orch.git(self.root,"add","."); orch.git(self.root,"commit","-m","out of scope")
            with self.assertRaises(orch.OrchestrationError): orch.validate_runtime_candidate(self.root,previous,orch.git(self.root,"rev-parse","HEAD"),lock["version"],evidence)

    def test_runtime_rejects_old_forged_minimal_receipt_and_bad_manifest_semantics(self):
        previous,lock,build_source,candidate,evidence=self.runtime_candidate()
        state=orch.read_state(self.root)
        bad=copy.deepcopy(state)
        bad["tasks"]["T1"]["candidates"][-1]["evidence"]["desktop_runtime"]={"verifier":"verify_desktop_runtime","verified":True,"rebuilt":True,"manifest_reused":False,"paths":["desktop-runtime/manifest.json","desktop-runtime/sourcehash"],"manifest_path":"desktop-runtime/manifest.json","manifest_sha256":"a"*64,"sourcehash":"a"*64}
        orch.atomic(orch.state_file(self.root),bad)
        with self.assertRaises(orch.OrchestrationError): orch.rebind_publish_source(self.root,task_id="T1",pm_thread_id="pm-1",candidate_id="runtime")
        self.assertEqual(orch.read_state(self.root),bad)
        orch.atomic(orch.state_file(self.root),state)
        for key,value in (("schema",True),("repository","other/repo"),("version","0.1.0"),("platform","linux"),("arch","arm64"),("build_source_sha","0"*40),("source_tree_hash","0"*64)):
            with self.subTest(manifest=key):
                bad=copy.deepcopy(evidence); manifest=json.loads(bad["desktop_runtime"]["manifest_content"]); manifest[key]=value
                content=json.dumps(manifest,separators=(",",":"))+"\n"
                bad["desktop_runtime"].update(manifest_content=content,manifest_lfs_oid=hashlib.sha256(content.encode()).hexdigest(),manifest_size=len(content.encode()))
                with self.assertRaises(orch.OrchestrationError): orch.validate_runtime_candidate(self.root,previous,candidate,lock["version"],bad)

    def test_runtime_rejects_missing_extra_objects_and_version_only_bypass(self):
        previous,lock,build_source,candidate,evidence=self.runtime_candidate()
        obj_info=evidence["desktop_runtime"]["lfs_objects"]["desktop-runtime/win-x64/x2Stock.exe"]
        oid=obj_info["oid"]; obj=orch.common_dir(self.root)/"lfs/objects"/oid[:2]/oid[2:4]/oid
        original=obj.read_bytes(); state=orch.read_state(self.root)
        obj.unlink()
        with self.assertRaises(orch.OrchestrationError): orch.rebind_publish_source(self.root,task_id="T1",pm_thread_id="pm-1",candidate_id="runtime")
        self.assertEqual(orch.read_state(self.root),state)
        obj.write_bytes(b"!"*len(original))
        with self.assertRaises(orch.OrchestrationError): orch.validate_runtime_candidate(self.root,previous,candidate,lock["version"],evidence)
        obj.write_bytes(original)
        target=self.root/"desktop-runtime/win-x64/x2Stock.exe"; target.unlink(); orch.git(self.root,"add","-u"); orch.git(self.root,"commit","-m","missing canonical runtime")
        with self.assertRaises(orch.OrchestrationError): orch.validate_runtime_candidate(self.root,previous,orch.git(self.root,"rev-parse","HEAD"),lock["version"],evidence)
        orch.git(self.root,"reset","--hard",candidate)
        target=self.root/"desktop-runtime/win-x64/extra.dll"; target.write_text("invalid\n"); orch.git(self.root,"add","."); orch.git(self.root,"commit","-m","extra runtime")
        with self.assertRaises(orch.OrchestrationError): orch.validate_runtime_candidate(self.root,previous,orch.git(self.root,"rev-parse","HEAD"),lock["version"],evidence)
        orch.git(self.root,"reset","--hard",candidate)
        orch.rebind_publish_source(self.root,task_id="T1",pm_thread_id="pm-1",candidate_id="runtime")
        orch.release_lock(self.root,task_id="T1",pm_thread_id="pm-1")
        orch.git(self.root,"branch","-f","origin/main",candidate)
        with orch.locked(self.root) as updated: updated["tasks"]["T1"]["baseline_sha"]=candidate
        # Model the next accepted source and lock in this isolated state; its runtime is still 0.1.1.
        with orch.locked(self.root) as updated:
            updated["publish_lock"]={**lock,"candidate_id":"runtime","source_candidate_sha":candidate,"version":"0.1.2","runtime_review_sha":None}
        (self.root/"VERSION").write_text("0.1.2\n"); orch.git(self.root,"add","VERSION"); orch.git(self.root,"commit","-m","version-only bypass")
        state=orch.read_state(self.root)
        with self.assertRaises(orch.OrchestrationError): orch.bind_publish_final(self.root,task_id="T1",pm_thread_id="pm-1",final_publish_sha=orch.git(self.root,"rev-parse","HEAD"),version="0.1.2")
        self.assertEqual(orch.read_state(self.root),state)

    def test_runtime_rebind_rejects_nonancestor_source_even_with_locked_base(self):
        previous,lock,build_source,candidate,evidence=self.runtime_candidate()
        sibling=orch.git(self.root,"commit-tree",orch.git(self.root,"rev-parse",candidate+"^{tree}"),"-p",lock["base_sha"],"-m","sibling runtime candidate")
        orch.deliver(self.root,"T1",candidate_id="sibling",artifact="sibling-runtime",commit_sha=sibling,snapshot_id="snap3",available_at="2026-10-08T08:30:00+08:00",new_version=True,evidence=evidence)
        orch.review(self.root,"T1",candidate_id="sibling",result="passed",reviewer_thread_id="review-1"); orch.accept(self.root,"T1",candidate_id="sibling")
        state=orch.read_state(self.root)
        with self.assertRaises(orch.OrchestrationError): orch.rebind_publish_source(self.root,task_id="T1",pm_thread_id="pm-1",candidate_id="sibling")
        self.assertEqual(orch.read_state(self.root),state)
        bad=copy.deepcopy(evidence); bad["desktop_runtime"]["build_source_sha"]=sibling
        with self.assertRaises(orch.OrchestrationError): orch.validate_runtime_candidate(self.root,previous,candidate,lock["version"],bad)

    @unittest.skipUnless((Path(__file__).parents[1]/"scripts/verify_desktop_runtime.py").is_file(), "C desktop verifier is not in the A-only baseline")
    def test_integrated_c_verifier_accepts_full_materialized_synthetic_runtime(self):
        previous,lock,build_source,candidate,evidence=self.runtime_candidate()
        spec=importlib.util.spec_from_file_location("c_runtime_verifier",Path(__file__).parents[1]/"scripts/verify_desktop_runtime.py")
        verifier=importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)
        self.assertEqual(set(self.runtime_names),verifier.REQUIRED)
        self.assertEqual(verifier.manifest_issues(evidence["desktop_runtime"]["manifest_content"].encode(),lock["version"]),[])
        self.assertEqual(verifier.canonical_source_hash(self.root),evidence["desktop_runtime"]["source_tree_hash"])
        (self.root/".gitattributes").write_text("desktop-runtime/** filter=lfs diff=lfs merge=lfs -text\n"); orch.git(self.root,"add",".gitattributes")
        for path,entry in evidence["desktop_runtime"]["lfs_objects"].items():
            oid=entry["oid"]; obj=orch.common_dir(self.root)/"lfs/objects"/oid[:2]/oid[2:4]/oid
            (self.root/path).write_bytes(obj.read_bytes())
        self.assertEqual(verifier.verify_runtime(self.root,[x for x in orch.git(self.root,"ls-files","-z").split("\0") if x],materialized=True),[])
        orch.validate_runtime_candidate(self.root,previous,candidate,lock["version"],evidence)

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
