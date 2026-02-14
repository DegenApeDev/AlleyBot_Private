# CODEX Full Project Audit

**Project:** AlleyBot  
**Date:** 2026-02-14  
**Auditor:** Codex/Cascade deep code audit  
**Scope:** Core runtime, plugin architecture, security controls, secrets/config, platform integrations, and testing posture.

---

## 1) Executive Summary

AlleyBot is feature-rich and operational, but it has **high regression risk** due to multi-mixin duplication, weak interface contracts, and inconsistent runtime configuration paths.

### Overall Assessment
- **Architecture maturity:** Medium
- **Security posture:** Medium (good intent, uneven enforcement)
- **Operational reliability:** Medium-Low under rapid iteration
- **Test/quality guardrails:** Medium-Low for plugin contract regressions

### Top Risks
1. **Plugin contract drift** can break runtime commands without compile-time or startup hard-fail protection.
2. **API endpoint drift** across mixins causes repeated breakages (same feature implemented in multiple places).
3. **Security controls exist but are inconsistent** between modules/entry points.
4. **Dependency drift** (runtime imports not guaranteed by requirements).

---

## 2) System Topology (What was audited)

### Core Runtime
- `alleybot_core.py` loads config, memory, and plugin manager @alleybot_core.py#31-71
- `PluginManager` dynamically imports and initializes plugins @plugin_manager.py#56-207
- Production event-driven runner in `src/main.py` @src/main.py#21-90

### Security Surface
- Root message redaction filter: `security_filter.py` @security_filter.py#10-191
- Agentic runtime security filter: `src/agentic/security_filter.py` @src/agentic/security_filter.py#22-397
- Telegram owner gate: `plugins/telegram/telegram.py` @plugins/telegram/telegram.py#24-27 and @plugins/telegram/telegram.py#179-187

### Integration Surface
- Moltx mixins (`api`, `wallet`, `messaging`, `engagement`)
- Clawbr plugin and mixins
- Other platform plugins and skills framework

### Quality Surface
- Unit test suite exists in `/tests` (phase-based tests)  
  (`test_fixes.py`, `test_phase2.py`, `test_phase3.py`, `test_phase4.py`, `test_phase5.py`)

---

## 3) Findings by Severity

## CRITICAL

### C1. Plugin contract breakages are not prevented by startup hard-fail checks
**Evidence:**
- Plugin import/load errors are logged but system continues @plugin_manager.py#204-207
- No explicit contract validation between plugin command references and implemented methods.

**Impact:**
- Bot appears “running” while key capabilities are missing (e.g., missing methods at runtime).
- User-facing commands fail only when invoked.

**Recommendation:**
1. Add startup plugin contract validation (required methods per plugin).
2. Fail startup (or mark unhealthy) if required production plugins fail load.
3. Add smoke tests for command bindings.

---

## HIGH

### H1. Multiple mixins implement overlapping platform behavior, causing endpoint drift regressions
**Evidence:**
- Moltx behavior is split across API/wallet/messaging/engagement mixins and has had endpoint mismatches.
- Example heartbeat behavior existed in multiple locations (recently fixed).

**Impact:**
- Fixing one code path does not fix others.
- Regressions recur after unrelated edits.

**Recommendation:**
- Define a **single source of truth per endpoint family** (e.g., only API mixin owns heartbeat/feed/search).
- Other mixins should call canonical methods, not duplicate request paths.

---

### H2. Dependency drift: runtime EIP-712 path requires `eth-account`, but not guaranteed in requirements
**Evidence:**
- `requirements.txt` does not include `eth-account` @requirements.txt#1-16
- Wallet linking imports from `eth_account` in Moltx wallet code.

**Impact:**
- Wallet linking fails in fresh environments with `ImportError`.

**Recommendation:**
- Add `eth-account` to `requirements.txt` (or pin in lockfile).
- Add startup dependency checks for critical plugins.

---

### H3. Telegram owner identity config is inconsistent between components
**Evidence:**
- Telegram plugin validates owner using `TELEGRAM_ADMIN_CHAT_ID` @plugins/telegram/telegram.py#25-27
- Production main initializes webhook owner via `TELEGRAM_OWNER_ID` with hardcoded fallback @src/main.py#49-50

**Impact:**
- Potential mismatch in authorization behavior depending on execution path.

**Recommendation:**
- Standardize to one env var (`TELEGRAM_ADMIN_CHAT_ID`) across all entrypoints.
- Remove hardcoded fallback IDs in production paths.

---

### H4. Domain allowlist check is vulnerable to substring bypass
**Evidence:**
- `_is_allowed_domain` uses `if domain in url` @src/agentic/security_filter.py#242-247

**Impact:**
- Malicious URLs containing allowed domain text can pass checks.

**Recommendation:**
- Parse URL host with `urllib.parse.urlparse`.
- Validate exact host or subdomain rules (`endswith('.trusted.tld')`).

---

## MEDIUM

### M1. Plugin class selection is first-match introspection, not explicit
**Evidence:**
- First subclass of `AlleyBotPlugin` is selected by reflection @plugin_manager.py#177-184

**Impact:**
- Import order/class ordering could select unintended class in complex modules.

**Recommendation:**
- Require explicit export (`PLUGIN_CLASS = ...`) or naming convention (`<Name>Plugin`).

---

### M2. Auto-generated default plugin config may mask desired operator intent
**Evidence:**
- Missing `plugin_config.json` triggers generation with many enabled plugins @plugin_manager.py#61-63 and @plugin_manager.py#77-154

**Impact:**
- Unexpected plugin startup behavior in new environments.

**Recommendation:**
- Ship a reviewed baseline config in repo.
- Add explicit warning and confirmation for first-run generation.

---

### M3. Security filter architecture is duplicated (root + agentic) with potential policy drift
**Evidence:**
- Root filter @security_filter.py#10-191
- Agentic filter @src/agentic/security_filter.py#22-397

**Impact:**
- Rules diverge over time; different code paths may enforce different protections.

**Recommendation:**
- Consolidate into one policy module with shared enforcement and tests.

---

### M4. JSON memory fallback may risk race/corruption under concurrent writes
**Evidence:**
- Core memory fallback writes JSON directly @alleybot_core.py#114-121

**Impact:**
- Potential data loss in concurrent/threaded plugin scenarios.

**Recommendation:**
- Prefer SQLite path consistently, or add file locking/atomic write strategy.

---

## LOW

### L1. Hardcoded owner display strings and non-configurable labels
**Evidence:**
- Owner display name string in Telegram plugin @plugins/telegram/telegram.py#27

**Impact:**
- Minor maintainability and portability issue.

**Recommendation:**
- Move all identity presentation to config.

---

## 4) Security Review Notes

### Strengths
- Owner-gated Telegram command handling exists and is applied in handlers @plugins/telegram/telegram.py#179-187
- Message redaction of sensitive values exists @security_filter.py#112-146
- Agentic security filter supports risk levels and approval callback @src/agentic/security_filter.py#13-19 and @src/agentic/security_filter.py#249-299

### Gaps
- URL/domain validation logic should be hardened (see H4).
- Security policy should be centralized to avoid divergence (see M3).
- Dependency and plugin health checks should block unsafe startup states.

---

## 5) Reliability & Regression Risk Analysis

Primary risk factors observed:
1. **Cross-cutting plugin edits with no contract tests**
2. **Mixin overlap where same feature can live in multiple files**
3. **Soft-failure plugin loader behavior**
4. **Inconsistent env var naming in runtime paths**

This explains recent recurring "worked before, now broken" behavior.

---

## 6) Recommended Remediation Plan (Prioritized)

### Phase A (Immediate, 1-2 days)
1. Add plugin startup contract checks (required methods per production plugin).
2. Add dependency guard (assert `eth-account` for Moltx wallet features).
3. Standardize Telegram owner env var usage.
4. Harden `_is_allowed_domain` with parsed hostname checks.

### Phase B (Short-term, 3-5 days)
1. Consolidate Moltx endpoint ownership into one canonical mixin layer.
2. Consolidate security filters into a single shared policy module.
3. Introduce plugin health status endpoint/report in dashboard.

### Phase C (Quality Guardrails, 1 week)
Add regression tests:
- Plugin import smoke test for all enabled plugins
- Command binding test (every exposed command callable exists)
- Moltx endpoint contract tests (heartbeat/status/wallet link flow)
- Security URL allowlist bypass test

---

## 7) Suggested Test Additions

1. **Plugin Load Smoke Test**
   - Iterate over enabled plugin config and assert load success.
2. **Command Map Integrity Test**
   - For every command in `get_commands`, callable must exist and execute no-op safely.
3. **Moltx Wallet Shape Test**
   - Verify wallet link handles both string and object `evm_wallet` response forms.
4. **Security URL Host Validation Test**
   - Block crafted URLs containing allowed domain as substring.

---

## 8) Final Verdict

AlleyBot is operational and feature-complete enough for active use, but **engineering reliability controls lag behind feature velocity**. The project should prioritize plugin contract enforcement and centralized endpoint/security ownership to stabilize future iterations.

**Audit Verdict:** ⚠️ **Usable in production with elevated regression risk**  
**Confidence:** High (based on direct source audit of core/runtime/security/plugin modules)

---

## 9) Appendix: Key Files Reviewed

- @alleybot_core.py#31-71
- @plugin_manager.py#56-207
- @src/main.py#21-56
- @plugins/telegram/telegram.py#24-27
- @plugins/telegram/telegram.py#179-187
- @security_filter.py#10-146
- @src/agentic/security_filter.py#22-247
- @requirements.txt#1-16
- Clawbr and Moltx plugin/mixin paths under `plugins/`

---

*Generated by Codex full-project audit pass.*
