# Tagger

An open-source, self-hostable PDF-to-iXBRL workspace for UK company and LLP
accounts. The intended workflow is conversion, free tagging with Cake's taxonomy
explorer, validation, review, export and authorised Companies House filing.

**Implementation status: Step 2, application foundation, is in progress.**
The local preview supports individual logins, private projects, team access,
immutable PDF storage, document-integrity jobs and appearance preferences.
[Start the local preview](docs/development/foundation.md).

Baseline feasibility is sufficient to start development; remaining qualification
has explicit later milestone ownership. The principal local fixture remains the
108-page Grant Thornton FY26 example, with all report content/output ignored.
Conversion, taxonomy tagging, iXBRL export and filing are not implemented in the
application yet. No profile is qualified for production filing.

- [Accepted implementation plan](docs/implementation-plan.md)
- [Current milestone and next work](docs/milestones/02-foundation.md)
- [Baseline evidence and retained qualification](docs/milestones/01-baseline.md)
- [Prior-project assessment](docs/intake-assessment.md)
- [Cake preservation contract](docs/architecture/cake-preservation.md)
- [Compliance sources and candidate profiles](docs/compliance/README.md)
- [Tool qualification and reproduction](docs/qualification/README.md)
- [Publication safeguards](docs/security/publication.md)

## Local checks

Python 3.12 or later; these checks require Git but no application dependencies:

```sh
python3 -m unittest discover -s tests/baseline -v
python3 -m tools.baseline.check
python3 -m tools.baseline.publication_guard --worktree
python3 -m tools.baseline.publication_guard
```

The final command checks **staged bytes**, including force-added ignored files.
The worktree command also checks public untracked files. Neither is a complete
secret/PII scan. They do not modify the index, install hooks, or publish anything.

Optional checks requiring local supplied materials or qualification tools are
documented in [qualification](docs/qualification/README.md). `--require-qualified`
intentionally fails until full qualification is satisfied;
`--require-foundation-ready` separately checks readiness to start foundation work; a passing unit test
run must never be presented as filing qualification.

## Licence

New Tagger code is licensed under **GPL-3.0-or-later**. See [LICENSE](LICENSE).
Third-party components, reference repositories, documents, taxonomy packages and
models retain their own terms. See [the licence inventory](docs/qualification/licences.md).
Downloaded tools and supplied reports are not part of the public source distribution.
