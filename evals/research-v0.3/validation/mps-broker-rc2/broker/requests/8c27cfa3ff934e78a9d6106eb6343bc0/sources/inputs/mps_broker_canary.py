"""Real worker-side regression for the full broker MPS environment.

Run only through the scientific broker, with a controller listening on the
provided loopback port and synthetic protected fixtures. No model calls and no
research measurements are involved. The script deliberately does not set or
repair either allocator variable: the broker must supply the valid pair.
"""
import argparse
import errno
import json
import math
import os
from pathlib import Path
import platform
import socket


def denied(operation):
    try:
        operation()
    except OSError as error:
        # Missing files and refused connections do not establish isolation.
        return error.errno in (errno.EPERM, errno.EACCES)
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--readonly', type=Path, required=True)
    parser.add_argument('--protected', type=Path, required=True)
    parser.add_argument('--port', type=int, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError('Use a new canary output directory')
    args.output.mkdir(parents=True)
    high = os.environ.get('PYTORCH_MPS_HIGH_WATERMARK_RATIO')
    low = os.environ.get('PYTORCH_MPS_LOW_WATERMARK_RATIO')
    assert high is not None and low is not None, 'The full broker must supply both watermarks'
    assert float(high) == .2 and float(low) == .1, 'Keep the validated memory limits unchanged'
    assert os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK') == '0'
    checks = {
        'readonly_input_read': args.readonly.read_text() == 'allagma readonly canary\n',
        'readonly_input_write_denied': denied(lambda: args.readonly.write_text('must not write')),
        'protected_read_denied': denied(lambda: (args.protected / 'answer.txt').read_text()),
        'outside_workspace_write_denied': denied(lambda: (args.protected / 'write.txt').write_text('must not write')),
    }
    def connect():
        with socket.create_connection(('127.0.0.1', args.port), timeout=2):
            pass
    checks['network_denied_with_permission_error'] = denied(connect)
    assert all(checks.values()), checks

    import torch
    import torch.nn.functional as functional

    torch.set_num_threads(1)
    torch.manual_seed(731)
    assert torch.backends.mps.is_available(), 'An actual MPS device is required'
    # Known-answer gradient, actually allocated and computed on MPS.
    x = torch.tensor([1., 2.], device='mps')
    w = torch.tensor([3., 4.], device='mps', requires_grad=True)
    loss = (x * w).sum().square()
    loss.backward()
    torch.mps.synchronize()
    checks['known_forward'] = loss.item() == 121.
    checks['known_gradient'] = torch.equal(w.grad.cpu(), torch.tensor([22., 44.]))

    features = torch.tensor([[1., 2., 3.], [-1., 0., 2.], [3., 1., -2.]], device='mps')
    targets = torch.tensor([[.1, .2], [.3, .4], [.5, .6]], device='mps')
    net = torch.nn.Sequential(torch.nn.Linear(3, 4), torch.nn.ReLU(), torch.nn.Linear(4, 2)).to('mps')
    optimizer = torch.optim.AdamW(net.parameters(), lr=.01, betas=(.9, .98), weight_decay=.1, foreach=False)
    def train(model, optim, count):
        values = []
        for _ in range(count):
            optim.zero_grad(set_to_none=True)
            value = functional.mse_loss(model(features), targets)
            value.backward()
            optim.step()
            values.append(value.item())
        return values
    losses = train(net, optimizer, 8)
    with torch.no_grad():
        before = net(features).cpu()
    checkpoint = args.output / 'checkpoint-8.pt'
    torch.save({'model': net.state_dict(), 'optimizer': optimizer.state_dict(), 'updates': 8}, checkpoint)
    losses.extend(train(net, optimizer, 4))
    with torch.no_grad():
        expected = net(features).cpu()
    saved = torch.load(checkpoint, map_location='cpu', weights_only=True)
    restored = torch.nn.Sequential(torch.nn.Linear(3, 4), torch.nn.ReLU(), torch.nn.Linear(4, 2)).to('mps')
    restored.load_state_dict(saved['model'])
    restored_optimizer = torch.optim.AdamW(restored.parameters(), lr=.01, betas=(.9, .98), weight_decay=.1, foreach=False)
    restored_optimizer.load_state_dict(saved['optimizer'])
    with torch.no_grad():
        restored_before = restored(features).cpu()
    checks['checkpoint_prediction_agreement'] = bool(torch.allclose(before, restored_before, atol=1e-6, rtol=1e-6))
    train(restored, restored_optimizer, 4)
    torch.mps.synchronize()
    with torch.no_grad():
        actual = restored(features).cpu()
    checks['resumed_training_agreement'] = bool(torch.allclose(expected, actual, atol=1e-6, rtol=1e-6))
    checks['finite_training'] = all(math.isfinite(v) for v in losses)
    checks['optimizer_updates'] = all(int(v['step']) == 12 for v in restored_optimizer.state.values())
    result = {'status': 'pass' if all(checks.values()) else 'fail', 'checks': checks,
              'backend': 'actual local MPS', 'torch': str(torch.__version__),
              'python': platform.python_version(), 'high_watermark': high, 'low_watermark': low,
              'checkpoint': str(checkpoint), 'maximum_resume_prediction_error': float((actual - expected).abs().max()),
              'scope': 'Complete broker environment, MPS allocation/forward/backward/AdamW/checkpoint/resume and actual filesystem/network denials. No native agent qualification, research-result claim, or instantaneous GPU-memory containment claim.'}
    (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    assert result['status'] == 'pass'


if __name__ == '__main__':
    main()
