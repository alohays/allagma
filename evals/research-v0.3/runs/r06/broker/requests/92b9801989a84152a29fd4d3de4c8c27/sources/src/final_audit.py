"""Source syntax audit and immutable historical evidence recovery."""
from pathlib import Path
import archive_analysis
import archive_preflight
import study as s


def main():
    sources = sorted(Path('src').glob('*.py'))
    for path in sources:
        compile(path.read_text(), str(path), 'exec')
    archive_analysis.main()
    archive_preflight.main()
    s.write_json('analysis/source-and-archive-audit.json', {
        'passed': True, 'syntax_checked_sources': [str(p) for p in sources],
        'historical_analysis_source_hash_verified': True,
        'historical_checkpoint_derived_metrics_exact': True})


if __name__ == '__main__':
    main()
