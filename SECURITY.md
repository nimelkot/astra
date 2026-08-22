# Security Policy

## Supported Versions

Security fixes are prioritized for the latest code on `main` and the active feature-development branch. Older commits and releases may not receive security updates.

## Reporting a Vulnerability

Please do not disclose suspected vulnerabilities in a public issue or pull request. Report them privately through GitHub's **Report a vulnerability** workflow on the repository Security tab:

https://github.com/nimelkot/astra/security/advisories/new

Include:

- A clear description of the issue and its potential impact
- The affected version, commit, or branch
- Reproduction steps or a minimal proof of concept
- Any relevant logs, stack traces, or suggested mitigation

Please avoid including secrets or personal data in the report. If the private advisory form is unavailable, contact the repository maintainer through GitHub before making any public disclosure.

## Response Process

The maintainer will acknowledge reports as soon as practical, reproduce and assess the issue, coordinate a fix, and publish remediation details with the reporter's agreement. Reporters will be credited unless they request anonymity.

Astra parses indexed files without importing or executing the target project. Nevertheless, users should treat MCP access and indexed workspace paths as sensitive capabilities and only connect trusted agents to repositories they are authorized to inspect.
