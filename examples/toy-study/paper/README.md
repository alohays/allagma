# Publish the retained toy result

Follow the [toy-to-paper walkthrough](../../../docs/guides/toy-to-paper.md) from
the small source checkout. It lists all inputs and executable commands, including
review failure/recovery and the separate optional TeX build.

`prepare.py` creates a new `publications/<revision>/` in a completed default toy.
It verifies the existing evidence, copies the editable sections/configuration,
binds actual result digests and creates pending review input. It does not rerun
experiments, edit the default report configuration, or approve the manuscript.
Select the anonymous attribution file explicitly or supply your own authors.

`record_review.py` records the reader's actual scientific and wording judgments
in a new review/configuration revision. It refuses pending or stale input and
never replaces a review. The existing paper checker and builder remain the
validation/build entry points. This helper cannot determine whether the supplied
judgments are true or independently reviewed.

The example is specific to the completed default `toy-v1` campaign and `a001`
analysis. Adapted and partial studies need their own paper inputs. Keep failed
publication/build directories and choose new revision names after a failure.
The `OUTLINE.md` describes the argument; `paper.example.json` holds JSON locators,
not replacement results. All seven final sections are prose with evidence macros.
No external literature, test-fixture bibliography or generated scientific result
is supplied by this example.
