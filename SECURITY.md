# Security policy

## Reporting a vulnerability

Please report credential exposure, unsafe agent behavior, or another security
issue through [GitHub private vulnerability reporting](https://github.com/antflydb/antfly-skills/security/advisories/new).
Do not include exploit details, credentials, or private source data in a public
issue or pull request.

If GitHub does not offer private reporting, ask for a private reporting channel
in an issue without disclosing the vulnerability or any sensitive information.

Include the affected commit or installed skill version, the relevant files,
reproduction steps with sanitized examples, and the expected security boundary.
If a credential was exposed, revoke or rotate it promptly; do not send the
credential with your report.

## Scope

This policy covers the instructions, scripts, and examples in this repository.
For vulnerabilities in an external product or runtime, use that project's
security reporting process.

Security fixes target the latest revision on `main`. Update installed Skills
with `npx skills update` and review relevant configuration changes.
