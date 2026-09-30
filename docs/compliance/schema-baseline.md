# Companies House transport schema baseline

Checked 29 September 2026. Twelve original XSD files are pinned locally; all four
selected roots compile without network access. Thirty synthetic checks cover
envelope, accounts wrapper and polling structure. This does not qualify an
accounts profile or constitute Companies House testing. No credentials were
loaded and no submission was attempted.

## Selected schemas

| Role | Root | Evidence and limitation |
|---|---|---|
| Envelope | `Egov_ch-v2-0.xsd` | Downloaded directly from the official host; not individually listed in the current status catalogue |
| Submission wrapper | `FormSubmission-v2-11.xsd` | Listed live; v2-10 is also listed live |
| Polling | `GetSubmissionStatus-v2-9.xsd` | Listed live; internal `version` attribute says `2.8` |
| Status acknowledgement | `GetStatusAck-v1-1.xsd` | Listed live; root element is `StatusAck`, not `GetStatusAck` |

Sources: [official catalogue](https://xmlgw.companieshouse.gov.uk/SchemaStatus),
[envelope](https://xmlgw.companieshouse.gov.uk/v1-0/schema/Egov_ch-v2-0.xsd),
[wrapper](https://xmlgw.companieshouse.gov.uk/v1-0/schema/forms/FormSubmission-v2-11.xsd),
[polling](https://xmlgw.companieshouse.gov.uk/v1-0/schema/forms/GetSubmissionStatus-v2-9.xsd),
[acknowledgement](https://xmlgw.companieshouse.gov.uk/v1-0/schema/forms/GetStatusAck-v1-1.xsd).
Exact downloaded bytes, namespaces, dependencies and the catalogue snapshot hash
are in [ch-schema-pins.json](ch-schema-pins.json). Hashes are observed acquisition
pins, not publisher signatures. Originals remain under ignored `.local/` storage.

Polling includes `baseTypes-v3-4.xsd`, while acknowledgement includes
`baseTypes-v1-1.xsd`. Preserve those exact references even though the catalogue
lists newer base types. The currency vocabulary aliases and their versioned
targets are pinned too. Each root is compiled independently; do not merge
different historical base-type definitions into one namespace indiscriminately.

## Findings that constrain implementation

1. **Test-mode lexical value.** The envelope defines `GatewayTest` as an integer.
   The local validator accepts `1`, `0` and `2`, and rejects `true` and `false`.
   The supplied filing TIS nevertheless says `true` in paragraphs 883 and 1650
   (paragraph numbering defined in the compliance README). Use explicit test and
   production application states, not arbitrary schema-valid integers. `1` is the
   schema-valid test candidate; confirm operational handling during the authorised
   test-account milestone. Schema testing does not settle the prose discrepancy
   on behalf of the gateway.
2. **Envelope validation is insufficient.** Its Body wildcard has
   `processContents="lax"`. The envelope alone accepts an unknown body and a
   malformed submission wrapper. Validate the body against its selected schema
   separately, then validate the decoded accounts and filing rules.
3. **Attachment bytes require separate checks.** A syntactically valid base64
   attachment containing synthetic non-accounts XML passes the wrapper schema.
   The locally installed lxml 6.1.1 / libxml2 2.14.6 also accepts some invalid
   base64 alphabet characters. A separate strict decoder rejects those cases.
   This is an observed local validator limitation, not a claim about the gateway's
   implementation. Require canonical base64 (allowing XML whitespace), size bounds,
   and decoded-payload validation. A wrapper pass proves neither iXBRL validity nor
   entity/account eligibility.
4. **Identifiers and response states are explicit.** The wrapper constrains
   `SubmissionNumber` to six characters. Its company type enumeration includes
   `EW`, `SC`, `NI`, `R`, `OC`, `SO`, `NC`; these technical codes do not establish
   accounting eligibility. Polling permits `ACCEPT`, `REJECT`, `PENDING`, `PARKED`
   and `INTERNAL_FAILURE`. Preserve them as distinct outcomes; never equate an
   envelope acknowledgement, parked state or internal failure with acceptance.

Implementation evidence: [probe and authored cases](../../tools/baseline/ch_schema_probe.py),
[local pin verification](../../tools/baseline/ch_schemas.py),
[actual test results](../qualification/ch-schema-result.json).

## Reproduce

Administrative acquisition, with no account or report involved:

```sh
python3 -m tools.baseline.ch_schemas --acquire
python3 -m tools.baseline.ch_schemas
```

Only the twelve pinned schema URLs are acquired; redirects remain restricted to
the official HTTPS schema host/path. Existing verified files are reused. Downloads
are bounded and must match exact hashes/sizes before replacement. Processing
never acquires missing dependencies.

Run the probe using the already installed local lxml interpreter:

```sh
/home/robert-marks/.pyenv/versions/3.12.8/bin/python -m tools.baseline.ch_schema_probe
```

The worker runs in an OS network namespace with a resolver restricted to the
verified local schema set. XML entity resolution and network loading are disabled.
The result records the actual lxml/libxml versions and extension binary hash.
Other environments must supply their own lxml interpreter and requalify it; this
is not yet a distributable production validator image.

`schema_checks_pass` means all expected positive, negative and permissiveness
observations matched. Some deliberately invalid application payloads are expected
to pass XSD and fail another layer. Read the per-case results rather than treating
the overall probe status as permission to file.

## Remaining baseline work

The transport-schema dependency gap is closed for these four roots. The following
remain separate: XBRL specification/conformance-suite pins, exact legal/framework
eligibility per company/LLP profile, complete positive/negative account fixtures,
and later Companies House test acceptance. Independent processor comparison is
optional and does not gate qualification. No
candidate profile has been enabled by this work.
