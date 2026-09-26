#!/usr/bin/env python
"""
Settle one record per domain against the workflow its model binds.

Every 4.4.0 model binds one ProvGov workflow, so a Cordova record carries a
current-state the Verifiable Settlement Layer can settle: sdcgovernance reads the
state machine from the published model (the XdOrdinal state clusters in the
workflow slot) and the current state from the record, and decides a proposed
transition with OASIS XACML semantics. For each domain this asks for the first
legal transition (PERMIT) and for a state the machine does not reach next (DENY),
and prints both decisions with their reasons. Nothing is staged: the model and a
generated record are the only inputs.

    python scripts/settle_demo.py            # reads app/sdc4/mediafiles/dmlib and app/sdc4/import_data
"""
from __future__ import annotations

import glob
import os
import re
import sys

from sdcgovernance import Decision, GovernanceEngine
from sdcgovernance.workflow import extract_workflow_from_model

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app", "sdc4")
DMLIB = os.path.join(ROOT, "mediafiles", "dmlib")
IMPORT = os.environ.get("CORDOVA_IMPORT_DIR") or os.path.join(ROOT, "import_data")


def records():
    """(domain title, xsd path, current state, file): one generated record per model, the first whose state has a next state."""
    for app in sorted(os.listdir(IMPORT)):
        files = sorted(glob.glob(os.path.join(IMPORT, app, "*.xml")))
        if not files:
            continue
        chosen = None
        for path in files[:200]:
            head = open(path, encoding="utf-8").read(4000)
            ct = re.search(r"dm-([a-z0-9]{24})", head).group(1)
            title = re.search(r"<dm-label>([^<]*)</dm-label>", head).group(1)
            state = re.search(r"<current-state>([^<]*)</current-state>", head)
            state = state.group(1) if state else ""
            xsd = os.path.join(DMLIB, f"dm-{ct}.xsd")
            if chosen is None:
                chosen = (title, xsd, state, path)
            tree = extract_workflow_from_model(xsd)
            if state and tree and tree.get_allowed_transitions(state):
                chosen = (title, xsd, state, path)
                break
        yield chosen


def main() -> int:
    failures = 0
    print(f"{'Domain':<32} {'current state':<22} {'proposed':<26} decision")
    for title, xsd, current, path in records():
        engine = GovernanceEngine(xsd)
        tree = extract_workflow_from_model(xsd)   # the state machine, read from the published model
        allowed = engine.get_allowed_transitions(current, workflow_tree=tree) if tree else []
        if not current or not allowed:
            print(f"{title:<32} {current or '(none)':<22} {'(terminal state)':<26} -")
            continue
        first = allowed[0]["target_symbol"]
        permit = engine.evaluate_transition(current_state=current, target_state=first, actor="cordova-settle-demo", workflow_tree=tree)
        reach = {t["target_symbol"] for t in allowed} | {current}
        symbols = sorted({s.symbol for p in tree.paths for s in p.states})
        skipped = next((s for s in symbols if s not in reach), None)   # a state the machine does not offer next
        deny = engine.evaluate_transition(current_state=current, target_state=skipped, actor="cordova-settle-demo", workflow_tree=tree) if skipped else None
        print(f"{title:<32} {current:<22} {'-> ' + first:<26} {permit.decision.name}")
        if deny is not None:
            print(f"{'':<32} {'':<22} {'-> ' + skipped:<26} {deny.decision.name}   {(deny.errors or [''])[0][:70]}")
        failures += permit.decision != Decision.PERMIT
        failures += deny is not None and deny.decision != Decision.DENY
    print()
    print("every first legal transition PERMIT, every skipped one DENY" if not failures else f"{failures} decisions were not as expected")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
