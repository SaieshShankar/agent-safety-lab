# Agent Safety Lab

Can a tool-using agent recognize that permission changed between opening a ticket and dispatching it? This Python evaluation harness measures two failure modes independently: acting after revocation and refusing work after approval.

## Reproduce the result

Python 3.10 or later is sufficient. Run these commands from the project root.

```sh
python demo.py
python -m unittest discover -v
```

Open **demo-output/comparison.html**. Each disagreement expands to show the assignment, registry update, customer note and both proposed actions. The demo also writes machine-readable results, raw episode traces and turn-level monitor scores. To keep a second run, use `python demo.py --out demo-output-2`.

## What the calibration establishes

Eight seed blocks each contain eight matched conditions. Two scripted agents handle the same 64 cases. One retains the initial permission. The other checks the newest registry event for the assigned ticket.

| Current authority | Cases | Initial-permission agent | Registry-aware agent |
| --- | ---: | --- | --- |
| Stable | 32 | 32 correct | 32 correct |
| Newly granted | 16 | 16 unnecessary holds | 16 correct dispatches |
| Revoked | 16 | 16 unsafe proposals | 16 correct holds |

A stable-only evaluation scores both agents 32/32. Adding permission changes exposes the stale agent's equal tendency to over-act and under-act. The demo checks these expected counts automatically. The results characterize scripted controls. Model-specific conclusions require independent model runs.

## Evaluate a model

```sh
python study.py run --model MODEL_ID --endpoint https://YOUR_HOST/v1/chat/completions --count 8 --out model-run
python study.py compare demo-output/registry model-run --html model-review.html
```

Use a compatible inference server and set `EVAL_API_KEY` in your environment if required. Keep provider settings fixed across comparisons. Each eight-seed run uses at most 128 model calls. Interrupted runs support `--resume` with the original configuration.

## How it works

1. The scenario generator crosses initial permission, current permission and agreement of the customer note. It also supplies a newer registry event for a different ticket.
2. The agent opens the assigned ticket and chooses a final operation. The simulator scores the raw response against current authority. All tool effects are synthetic.
3. A separate monitor receives only evidence available before the proposed action. The scorer checks alert coverage and calculates a confusion matrix.
4. The report compares matching case IDs and exposes missing coverage. Raw traces support replay and inspection of individual decisions.

| Entry point | Purpose |
| --- | --- |
| `study.py` | Run, resume and compare the authorization-update study |
| `dispatch_monitor.py` | Reference prospective monitor for dispatch decisions |
| `research.py` | Multi-turn evaluation of disclosure, approval and persistence with observation or enforcement |
| `sandbox.py` | Single-decision calibration with missing-response accounting |

The benchmark varies identifiers and event order within fixed templates. A high score cannot establish deployment safety or generalization to unseen task families. See the [evaluation protocol](docs/protocol.md) for the schemas, scoring rules and limitations.
