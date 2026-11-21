import argparse
import copy
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
import research as r

class Tests(unittest.TestCase):
    def trial(self, profile="credulous", mode="observe", surface="approval", challenge=True):
        args=argparse.Namespace(model=None,profile=profile,mode=mode)
        return r.run_episode(args,0,surface,challenge,None)

    def test_matrix(self):
        for surface in r.SURFACES:
            for challenge in (True,False):
                for mode in ("observe","enforce"):
                    for profile in ("reference","credulous","refusal"):
                        rec=self.trial(profile,mode,surface,challenge)
                        scores=r.evidence(rec)
                        unsafe=profile=="credulous" and challenge
                        self.assertEqual(scores["attempt"],unsafe)
                        self.assertEqual(scores["harm"],unsafe and mode=="observe")
                        if profile=="reference":
                            self.assertTrue(scores["clean_success"])
                        if profile=="refusal":
                            self.assertFalse(scores["utility"])
                        r.replay(rec,mode)

    def test_pairs(self):
        runs=[self.trial(challenge=c) for c in (False,True)]
        row=next(v for v in r.analyze(runs,2) if v["surface"]=="approval")
        self.assertEqual((row["paired_n"],row["paired_attempt_delta"]),(1,1))
        runs[0]["end"]="provider_error/OSError"
        row=next(v for v in r.analyze(runs,2) if v["surface"]=="approval")
        self.assertIsNone(row["paired_attempt_delta"])

    def test_trace_integrity(self):
        record=self.trial()
        for key,value in (("decision","finished"),("raw","{}"),("violations",[])):
            changed=copy.deepcopy(record)
            changed["history"][1][key]=value
            with self.assertRaises(ValueError):
                r.replay(changed,"observe")

    def test_invalid(self):
        for text in ('[]','{"op":"send","op":"read"}','{"op":3}',"junk"):
            self.assertIsNone(r.parse_action(text))

    def test_http(self):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                answer='{"op":"read"}' if len(body["messages"])==2 else '{"op":"finish"}'
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({"choices":[{"message":{"content":answer}}]}).encode())
            def log_message(self,*args):
                pass
        with HTTPServer(("127.0.0.1",0),Handler) as server:
            threading.Thread(target=server.serve_forever,daemon=True).start()
            try:
                args=argparse.Namespace(model="test",mode="observe",endpoint=f"http://127.0.0.1:{server.server_port}/chat/completions")
                rec=r.run_episode(args,5,"approval",False,r.model_call)
                self.assertEqual([t["decision"] for t in rec["history"]],["observed","finished"])
            finally:
                server.shutdown()

if __name__=="__main__":
    unittest.main()
