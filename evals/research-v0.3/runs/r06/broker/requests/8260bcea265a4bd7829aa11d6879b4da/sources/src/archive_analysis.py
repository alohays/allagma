"""Retain and hash-check the two analysis source revisions used by this study."""
import hashlib
import json
from pathlib import Path


def main():
    current = Path('src/analyze.py').read_text()
    old = current
    added = """    independent_metrics = metrics_from_arrays({**a, 'logits': independent,
                                               'predictions': independent.argmax(1)})
    centered_error = float(np.max(np.abs((independent - independent.mean(1, keepdims=True)) -
                                         (a['logits'].astype(np.float64) - a['logits'].astype(np.float64).mean(1, keepdims=True)))))
"""
    assert added in old
    old = old.replace(added, '')
    added = """            'numpy_float64_max_centered_logit_error': centered_error,
            'numpy_float64_forward_metrics': independent_metrics,
            'numpy_float64_forward_metric_differences': {k: independent_metrics[k] - recomputed[k] for k in recomputed},
"""
    assert added in old
    old = old.replace(added, '')
    added = """            'diagnostics_posthoc': {'input_weight_l2': float(np.linalg.norm(wi.astype(np.float64))),
                                   'output_weight_l2': float(np.linalg.norm(wo.astype(np.float64))),
                                   'min_logit': float(a['logits'].min()), 'max_logit': float(a['logits'].max()),
                                   'max_abs_row_mean_logit': float(np.abs(a['logits'].astype(np.float64).mean(1)).max())},
"""
    assert added in old
    old = old.replace(added, '')
    old = old.replace("                ax.set_xticks([0, 1000, 10000, 100000], ['0', '1,000', '10,000', '100,000'])\n", '')
    old = old.replace("    handles, labels = axes[0, 0].get_legend_handles_labels()\n    fig.legend(handles, labels, fontsize=9, loc='upper center', bbox_to_anchor=(.5, .97), ncol=4)\n",
                      "    axes[0, 0].legend(fontsize=8, loc='center right')\n")
    old = old.replace("    fig.tight_layout(rect=(0, 0, 1, .935))\n", "    fig.tight_layout(rect=(0, 0, 1, .975))\n")
    expected = json.loads(Path('analysis/preflight/results.json').read_text())['analysis_source_sha256']
    assert hashlib.sha256(old.encode()).hexdigest() == expected
    folder = Path('provenance/sources')
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'analyze-preflight.py').write_text(old)
    (folder / 'analyze-final.py').write_text(current)
    print('Archived exact preflight analysis source and current final analysis source.')


if __name__ == '__main__':
    main()
