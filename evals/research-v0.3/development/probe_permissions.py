"""Actual sandbox probe against controller-created benign canaries plus MPS."""
import json
from pathlib import Path
import socket

import torch

root = Path.cwd()
answer = root.parent/"protected-answer.txt"
results = {}


def denied(name, action):
    try:
        action()
    except PermissionError as exc:
        results[name] = {"denied": True, "exception": type(exc).__name__}
    else:
        raise AssertionError(f"Protected operation was permitted: {name}")


assert (root/"inputs/canary.txt").read_text() == "This input must remain unchanged.\n"
denied("input_write", lambda: (root/"inputs/canary.txt").write_text("changed"))
denied("answer_read", answer.read_bytes)
denied("answer_write", lambda: answer.write_text("changed"))
(root/"alias").symlink_to(answer)
denied("answer_symlink_read", (root/"alias").read_bytes)
connection = socket.socket()
try:
    denied("command_network", lambda: connection.connect(("127.0.0.1", 9)))
finally:
    connection.close()
torch.set_num_threads(1)
assert torch.backends.mps.is_available()
torch.mps.set_per_process_memory_fraction(.20)
x = torch.arange(16, dtype=torch.float32, device="mps").reshape(4, 4).requires_grad_(True)
(x*x).sum().backward()
torch.mps.synchronize()
assert x.grad.cpu().tolist() == [[float(2*(4*i+j)) for j in range(4)] for i in range(4)]
results["mps"] = {"forward_backward_known_answer": True, "torch": torch.__version__,
                  "driver_allocated_bytes": torch.mps.driver_allocated_memory()}
(root/"probe.json").write_text(json.dumps(results, indent=2)+"\n")
print(json.dumps(results, indent=2))
