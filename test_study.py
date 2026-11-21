import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import study as s

class StudyTests(unittest.TestCase):
    def args(self,p="registry",out=None):
        return argparse.Namespace(profile=p,model=None,endpoint=None,out=out,seed=0,count=2,resume=False)

    def test_design(self):
        jobs=s.jobs(3,4)
        self.assertEqual(len(set(jobs)),32)
        for key in jobs:
            a=s.scenario(key)
            b=s.scenario((*key[:3],not key[3]))
            self.assertEqual(a["initial"],b["initial"])
            self.assertEqual(a["packet"]["registry_events"],b["packet"]["registry_events"])
            self.assertNotEqual(a["packet"]["requester_note"],b["packet"]["requester_note"])

    def test_shortcuts(self):
        for p,expected,unsafe in (("registry",32,0),("stale",16,8),("requester",16,8),("always-hold",16,0),("wrong-ticket",0,16)):
            vs=[s.verdict(s.play(k,self.args(p))) for k in s.jobs(10,4)]
            self.assertEqual((sum(v in s.PASS for v in vs),sum(v in s.UNSAFE for v in vs)),(expected,unsafe))

    def test_invalid_and_premature(self):
        k=(0,False,True,False)
        for raw,want in [('{"op":"dispatch","ticket":"x","to":"x"}',"premature_dispatch"),("bad","invalid"),('{}',"invalid")]:
            self.assertEqual(s.verdict({"key":k,"raw":[raw]}),want)
        with self.assertRaises(ValueError):
            s.verdict({"key":k,"raw":[s.dump(s.fixture("registry",s.scenario(k),0))]})

    def test_resume_and_partial_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=self.args(out=Path(tmp)/"left")
            b=self.args("stale",Path(tmp)/"right")
            s.run(a)
            s.run(b)
            path=next(p for p in b.out.glob("*.json") if p.name!="manifest.json")
            contents=path.read_bytes()
            path.unlink()
            report=s.compare(a.out,b.out,None)
            self.assertEqual(report["slices"]["All matched"]["n"],15)
            b.resume=True
            s.run(b)
            self.assertEqual(path.read_bytes(),contents)
            report=s.compare(a.out,b.out,Path(tmp)/"view.html")
            self.assertEqual(report["slices"]["All matched"]["left_only"],8)
            b.profile="registry"
            with self.assertRaises(ValueError):
                s.run(b)

    def test_incomplete_provider_response(self):
        a=self.args()
        a.model="mock"
        def invalid(args,messages):
            return "I cannot parse this."
        rec=s.play((0,False,False,False),a,invalid)
        self.assertEqual(s.verdict(rec),"invalid")
