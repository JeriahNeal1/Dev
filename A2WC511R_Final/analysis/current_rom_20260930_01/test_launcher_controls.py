"""In-memory tests only: no child executable, authorization file or provider."""
from pathlib import Path
import copy
import hashlib
import json

p = Path(__file__).resolve().with_name("launch_probe_once.py")
ns = {"__file__": str(p), "__name__": "offline_launcher_test"}
exec(compile(p.read_text(), str(p), "exec", optimize=2), ns)
gates = {
    "qualification_sha256": "sealed", "probe_invocation_count": 0, "launch_reserved": False,
    "completed_pre_probe_gates": [{"gate": x, "reply": "DONE " + x, "source": "user"} for x in ("G06", "G07", "G08")]
    + [{"gate": "G09", "reply": "TESTMODE G09 CEL AND FUEL-PUMP CYCLING", "source": "user", "test_mode_confirmed": True}],
    "commit_authorization": {"reply": ns["TOKEN"], "source": "user", "received_utc": "SYNTHETIC_TEST_ONLY_NOT_AUTHORIZATION"},
    "engine": "OFF", "stationary": True, "charger": "SCHUMACHER_SE_5212A_10A_CHARGING",
    "adapter": "GENUINE_OPENPORT_2_0", "operator_monitors_voltage": True, "full_acquisition_allowed": False,
}
ns["validate_gate"](gates, "sealed")
mutations = [
    ("probe_invocation_count", 1), ("launch_reserved", True), ("qualification_sha256", "different"),
    ("engine", "ON"), ("stationary", False), ("charger", "50A_ENGINE_START"), ("adapter", "unknown"),
    ("operator_monitors_voltage", False), ("full_acquisition_allowed", True), ("completed_pre_probe_gates", []),
    ("commit_authorization", {"reply": "PROCEED RK02", "source": "user", "received_utc": "fixture"}),
    ("commit_authorization", {"reply": ns["TOKEN"], "source": "assistant", "received_utc": "fixture"}),
]
for key, value in mutations:
    bad = copy.deepcopy(gates)
    bad[key] = value
    try:
        ns["validate_gate"](bad, "sealed")
    except (RuntimeError, KeyError):
        pass
    else:
        raise RuntimeError("Gate accepted mutation: " + key)


class FakeChild:
    def __init__(self):
        self.wait_count = 0

    def wait(self):
        self.wait_count += 1
        return 1


for fail in (False, True):
    child = FakeChild()

    def record_started():
        if fail:
            raise OSError("Injected bookkeeping failure")

    status, error = ns["wait_for_child"](child, record_started)
    assert child.wait_count == 1 and status == 1 and bool(error) == fail

result = {
    "status": "PASS_FINAL_OFFLINE_LAUNCHER_CONTROLS", "negative_gate_cases": len(mutations),
    "lifecycle_cases": 2, "positive_gate_cases": 1, "optimized_python_guards_active": True,
    "physical_launches": 0, "provider_loads": 0, "authorization_files_created": 0,
    "source": {"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()},
    "test_source": {"path": __file__, "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
    "limits": "Gate and child-wait logic tested in memory. Physical launch and provider loading not exercised.",
}
with p.with_name("LAUNCHER_FINAL_TESTS.json").open("x", encoding="utf-8") as f:
    json.dump(result, f, indent=2)
    f.write("\n")
print(json.dumps(result))
