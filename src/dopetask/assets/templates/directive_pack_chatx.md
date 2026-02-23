<!-- directive-pack:chatx@v1 -->
## ChatX Directives (Add-on, Minimal)

This pack is additive.
This pack does not override TaskX pack; if conflict, TaskX wins.

1. Case Bundle audit mode requirements:
2. Perform deep audit of recent packets, runs, evidence artifacts, and repo logs.
3. Diagnose systemic issues, including repeated failures, policy drift, and verification gaps.
4. Prefer deterministic diagnosis first (counts, diffs, missing files, failed gates) before LLM inference.
5. Produce sequential task packets that target root causes, not symptoms.
6. Keep packet scopes narrow and verification steps explicit.
7. Supervisor must maintain these outputs:
8. `CASE_AUDIT_REPORT.md` for human-readable diagnosis.
9. `CASE_FINDINGS.json` for structured findings.
10. `PACKET_RECOMMENDATIONS.json` for deterministic next steps.
11. Packet queue sequencing:
12. Order recommendations so prerequisites execute before dependent fixes.
13. Avoid parallel packet recommendations when they touch the same ownership boundary.
14. Meta hygiene:
15. Never rewrite existing packet contract text unless explicitly authorized.
16. Localize changes to meta-layer guidance and audit artifacts.
17. Do not weaken TaskX verification and evidence requirements.
18. If evidence is insufficient:
19. Mark `UNKNOWN`.
20. List missing artifacts.
21. Recommend deterministic bundle re-export requirements.
22. Optional prompt-pack output is allowed only as additive guidance with no contract override.
