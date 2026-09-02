# Security Policy

OmniAgent AI is designed for enterprise deployment with strict security, tenant isolation, and deterministic execution boundaries.

## Supported Versions
| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting Vulnerabilities
If you discover a potential security vulnerability, please do NOT create a public GitHub issue.
Instead, email security concerns directly to: **security@omniagent.ai**

Please include:
1. Description of the vulnerability and impact.
2. Steps to reproduce or proof-of-concept.
3. Potential remediations if known.

We acknowledge receipt within 48 hours and provide remediation status updates regularly.

## Security Architecture Principles
1. **Zero Trust & Defense in Depth**: Strict token authentication (JWT), RBAC authorization, and tenant isolation on all requests.
2. **Deterministic Tool Boundaries**: No agent has direct unrestricted access to databases or external services. All actions execute through registered tools with permission scopes.
3. **Human-in-the-Loop Approval**: High-risk actions (e.g. database mutations, financial disbursements, mass emails) mandate human approval before execution.
4. **Tamper-Proof Audit Logging**: Every agent step, tool invocation, and decision path is immutably logged with structured metadata.
5. **No Secret Commits**: Secrets must strictly reside in environment variables or cloud secret managers.
