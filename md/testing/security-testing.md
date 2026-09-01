# Testing — Security Testing, Prompt Red-Teaming & Fuzzing

## Status
**Status:** ✅ IMPLEMENTED (Bandit, Semgrep, OWASP Top 10 for LLMs & Red-Teaming)

---

## 1. Security Verification Toolchain

* **Static Application Security Testing (SAST):** `bandit -r backend/app` scans for unsafe python constructs, hardcoded secrets, and SQL injections.
* **Dependency Vulnerability Scanning:** `pip-audit` and `npm audit` check for CVE vulnerabilities in third-party packages.
* **Automated Red-Teaming Suite:** Automated adversarial injection tests (`tests/security/test_prompt_injections.py`) attempt 50+ known jailbreaks (e.g., DAN, Base64 obfuscation, recursive instruction injection). All tests must fail to alter agent behavior.

---

## 2. OWASP Top 10 for LLMs Verification Matrix

| OWASP Threat ID | Description | Test Method | Test Status |
| :--- | :--- | :--- | :---: |
| **LLM01: Prompt Injection** | Direct and indirect prompt hijacking. | Adversarial document red-team tests. | ✅ PASS |
| **LLM02: Insecure Output** | Unvalidated agent outputs mutating DBs. | Schema validation & AST SQL tests. | ✅ PASS |
| **LLM03: Training Data Poisoning**| RAG knowledge store poisoning. | Tenant isolation & admin ingestion tests. | ✅ PASS |
| **LLM06: Sensitive Information**| PII & secret key leakage in completions. | Regex PII leak scanner assertions. | ✅ PASS |
| **LLM08: Excessive Agency** | Autonomous unapproved destructive tool execution. | High-risk approval gate intercept tests. | ✅ PASS |
