# Design lineage and local adaptation

The supplied 6 October 2026 audit identified the mechanisms below. This is a
design adoption map, not copied code, a new exhaustive upstream audit or a
claim that the upstream runtimes are installed. The module manifests preserve
their relevant source identities.

| Source mechanism | Pinned source | Allagma adaptation |
| --- | --- | --- |
| ARIS workflow composition | [research-pipeline](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep/blob/5895d19a1d2ea529875fff999320ad83392169c2/skills/research-pipeline/SKILL.md) | Independent methods; default recipe includes manuscript writing |
| ARIS focused/permanent context | [project files guide](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep/blob/5895d19a1d2ea529875fff999320ad83392169c2/docs/PROJECT_FILES_GUIDE.md) | Replaceable context selector with persistent evidence |
| ARIS canonical integration | [integration contract](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep/blob/5895d19a1d2ea529875fff999320ad83392169c2/skills/shared-references/integration-contract.md) | One method source, thin host wrappers |
| ARIS maintenance from use | [meta-optimize](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep/blob/5895d19a1d2ea529875fff999320ad83392169c2/skills/meta-optimize/SKILL.md) | Usage feedback → candidate → comparison → decision |
| RRSI open edit space | [components.py](https://github.com/google-research/rrsi/blob/be50316e1db05914068a973f322770ef08ed7ba1/rrsi/components.py) | Methods, recipes and adapters can all change |
| RRSI domain separation | [domain.py](https://github.com/google-research/rrsi/blob/be50316e1db05914068a973f322770ef08ed7ba1/rrsi/domain.py) | Study science and framework evaluation have separate owners |
| RRSI failure history | [history.py](https://github.com/google-research/rrsi/blob/be50316e1db05914068a973f322770ef08ed7ba1/rrsi/history.py) | Preserve rejected and unevaluated candidates |
| RRSI cost-aware selection | [selection.py](https://github.com/google-research/rrsi/blob/be50316e1db05914068a973f322770ef08ed7ba1/rrsi/selection.py) | Consider noise, cost and complexity; do not copy benchmark coefficients |
| AntOmniEvo execution/evaluation separation | [system.py](https://github.com/ant-research/AntOmniEvo/blob/19008bd45963c1dce17a11c086b28a643774ac12/antomnievo/interface/system.py) and [evaluator.py](https://github.com/ant-research/AntOmniEvo/blob/19008bd45963c1dce17a11c086b28a643774ac12/antomnievo/interface/evaluator.py) | Replaceable execution and reviewer contracts |
| AntOmniEvo strategy boundary | [evolution_algorithm.py](https://github.com/ant-research/AntOmniEvo/blob/19008bd45963c1dce17a11c086b28a643774ac12/antomnievo/interface/evolution_algorithm.py) | External optimizers need explicit adapters/recipes; no assumed RRSI interchangeability |
| AntOmniEvo candidate files | [tunable_artifact_schema.py](https://github.com/ant-research/AntOmniEvo/blob/19008bd45963c1dce17a11c086b28a643774ac12/antomnievo/model/tunable_artifact_schema.py) | Candidate packages and decision lineage are inspectable files |

ARIS's model, venue, score thresholds and approval policy are not inherited.
RRSI's incumbent adoption differs from AntOmniEvo's parent selection/population
elimination. The comparison here is directed and deterministic; neither complete
optimizer is implemented or required.

Agent Skills supplies the packaging format. Copier's three-way migration idea,
uv's separation of intent from locked resolution, and nf-core's reviewable
update diffs inform the distribution protocol. Their packages are not mandatory
dependencies. See the [reference decision record](specification/allagma-reference-decisions-2026-10-06.md)
and [notices](../THIRD_PARTY_NOTICES.md).
