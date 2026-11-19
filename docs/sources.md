# Supporting references

These references inform the proposed design. They are not evidence that this
Company has been implemented or that a particular SaaS meets its objectives.

- [Paperclip Agent Companies specification][paperclip]: package conventions for
  `COMPANY.md`, role instructions, skills, and vendor runtime extensions. Checked
  against the local `paperclip/docs/companies/companies-spec.md` checkout.
- [Google SRE: error-budget policy][budget]: a concrete example of using service
  reliability to govern release activity.
- [Google SRE: canary releases][canary]: staged qualification and measurement
  before broad exposure.
- [AWS: failure management][failure]: recovery preparation and testing.
- [AWS: periodic recovery testing][restore]: measuring recovery against RTO/RPO.

The neighboring `pcc-aoc-solver-scala` package was inspected only for local
Company/agent/skill conventions. Its puzzle workflow, credentials, runtime
configuration, schedules, and deployments are not copied into this Company.

[paperclip]: https://github.com/paperclipai/paperclip/blob/master/docs/companies/companies-spec.md
[budget]: https://sre.google/workbook/error-budget-policy/
[canary]: https://sre.google/workbook/canarying-releases/
[failure]: https://docs.aws.amazon.com/wellarchitected/2024-06-27/framework/rel-failmgmt.html
[restore]: https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_backing_up_data_periodic_recovery_testing_data.html
