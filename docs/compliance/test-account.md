# External dependencies

The user confirmed on 28 September 2026 that **a Companies House test presenter
account is available**. A new application is unnecessary. No credentials were
requested, stored, tested or used by the baseline probes.

| Dependency | State | Next action |
|---|---|---|
| CH test presenter account | User-confirmed; connectivity untested | Configure through private secret storage at the test-filing milestone |
| CH profile testing | Not started | Agree cases and submit authorised synthetic examples; retain final outcomes |
| RaptorXML+XBRL | No local executable/licence available | Obtain local evaluation/licensed access and pin it before independent validation |
| Official FRC 2026 package | Published download identified | Acquire, hash and test offline closure |
| Production access/authority | Not established | Separate setup and explicit per-filing authorisation |

[Companies House developer guidance](https://www.gov.uk/government/publications/technical-interface-specifications-for-companies-house-software/important-information-for-software-developers-read-first)
requires unique envelope numbers and status polling. Applicable test attachments
can remain pending for manual review. Account availability is not testing completion.
No messages are sent to Companies House without explicit instruction.

The independent processor is a test dependency, not a bundled runtime. Do not
substitute a third-party report-validation service for local validation without
changing the confidentiality agreement.
