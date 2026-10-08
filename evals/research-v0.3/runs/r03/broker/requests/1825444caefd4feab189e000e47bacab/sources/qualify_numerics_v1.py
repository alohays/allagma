"""Independent numerical and checkpoint qualification using pilot seed 61."""
import json
from pathlib import Path
import platform
import time
import study as s

s.deps()
np, torch, F = s.np, s.torch, s.F
pairs, labels, train, test = s.data(61)
torch.manual_seed(61)
model = s.Net()
x = s.inputs(pairs[train], 'cpu', 'dense')
y = torch.as_tensor(labels[train])
wi = model.input.weight.detach().numpy().astype(np.float64)
wo = model.output.weight.detach().numpy().astype(np.float64)
xx = x.numpy().astype(np.float64)
pre = xx @ wi.T
h = np.maximum(pre, 0)
z = h @ wo.T
z -= z.max(axis=1, keepdims=True)
prob = np.exp(z)
prob /= prob.sum(axis=1, keepdims=True)
loss_np = -np.log(prob[np.arange(len(y)), y.numpy()]).mean()
err = prob.copy()
err[np.arange(len(y)), y.numpy()] -= 1
err /= len(y)
go = err.T @ h
gi = ((err @ wo) * (pre > 0)).T @ xx
loss = F.cross_entropy(model(x), y)
loss.backward()
grad_input_error = float(np.max(np.abs(gi-model.input.weight.grad.numpy())))
grad_output_error = float(np.max(np.abs(go-model.output.weight.grad.numpy())))
loss_error = abs(loss_np-float(loss.detach()))
assert loss_error < 2e-6 and max(grad_input_error,grad_output_error) < 2e-8
opt = torch.optim.AdamW(model.parameters(), lr=.001, betas=(.9,.98), eps=1e-8, weight_decay=1, foreach=False)
opt.step()
# At the first update the bias-corrected first and second moments equal g and g^2.
wi_after = wi*(1-.001)-.001*gi/(np.abs(gi)+1e-8)
wo_after = wo*(1-.001)-.001*go/(np.abs(go)+1e-8)
adam_error = max(float(np.max(np.abs(wi_after-model.input.weight.detach().numpy()))),
                 float(np.max(np.abs(wo_after-model.output.weight.detach().numpy()))))
assert adam_error < 2e-6, adam_error

def step(m, o):
    o.zero_grad(set_to_none=True)
    F.cross_entropy(m(x),y).backward()
    o.step()

for _ in range(9):
    step(model,opt)
scratch=Path('artifacts/qualification-resume.pt')
s.save_checkpoint(scratch,model,opt,10,{},[])
for _ in range(10):
    step(model,opt)
ck=torch.load(scratch,weights_only=False)
other=s.Net()
other.load_state_dict(ck['model'])
other_opt=torch.optim.AdamW(other.parameters(),lr=.001,betas=(.9,.98),eps=1e-8,weight_decay=1,foreach=False)
other_opt.load_state_dict(ck['optimizer'])
for _ in range(10):
    step(other,other_opt)
assert all(torch.equal(a,b) for a,b in zip(model.parameters(),other.parameters()))
assert torch.equal(model(x),other(x))

# Paired initialization and splits use independent, specified RNG streams.
init_hashes=[]
for wd in [0,1]:
    torch.manual_seed(61)
    m=s.Net()
    init_hashes.append(s.hashlib.sha256(b''.join(v.detach().numpy().tobytes() for v in m.parameters())).hexdigest())
assert init_hashes[0]==init_hashes[1]
assert all(np.array_equal(a,b) for a,b in zip(s.data(61),s.data(61)))
report=dict(status='passed',seed=61,heldout_used_for_optimization=False,
    independent_reference='NumPy float64 analytic forward, cross-entropy, gradients and first AdamW update',
    loss_abs_error=loss_error,gradient_input_max_abs_error=grad_input_error,
    gradient_output_max_abs_error=grad_output_error,first_adamw_update_max_abs_error=adam_error,
    resume='20 updates continuous vs 10+reload+10: bitwise equal parameters and logits',
    paired_initialization_sha256=init_hashes,platform=platform.platform(),machine=platform.machine(),
    python=platform.python_version(),torch_version=torch.__version__,numpy_version=np.__version__,
    source_revision=s.revision(),qualification_source_sha256=s.sha(__file__))
s.dump('artifacts/numerical-qualification.json',report)
print(json.dumps(report,indent=2))
