# ClauseDesk — Ethics Appendix

**Scope:** This appendix documents the ethical design decisions of
ClauseDesk v1. It supplements the product one-pager and is reviewed
at every architectural milestone.

**Last updated:** 2026-10-30

---

## 1. Data classes

### 1.1 What data we process

| Data category | Source | Sensitivity | Contains PII? |
|---|---|---|---|
| **CUAD contracts** | Public dataset (HuggingFace) | Low | No (public) |
| **User account** | Self-registration | Medium | Yes (email) |
| **User-uploaded contracts** | Upload endpoint | **High** | **Yes** (names, addresses, financial terms, signatures) |
| **Extraction results** (clauses, quotes) | Derived from uploads | High | Yes (quotes contain text from contract) |
| **LLM API requests/responses** | Sent to OpenAI / Groq | High | Yes (full contract text + extracted quotes) |
| **Application logs** | Server-side | Medium | No (PII redacted before logging — see §3) |
| **Review actions** | User actions on clauses | Medium | No (user_id only, no content) |

### 1.2 What we do NOT collect

- No legal entity information beyond what's in the contract
- No IP addresses retained beyond request duration
- No browsing history, cookies, analytics
- No biometric data, health data, or special-category data (GDPR Art. 9)

---

## 2. Consent & retention

### 2.1 Consent

- **Upload = explicit consent** to process the contract for extraction and human review purposes only.
- **Consent notice** shown before first upload: "Your contract will be sent to OpenAI (or Groq) for extraction. Stored for 30 days, then deleted. No training on your data."
- **Third-party processors** (OpenAI, Groq, hosting provider) disclosed in the consent notice and README.

### 2.2 Retention

| Data | Retention | Deletion |
|---|---|---|
| Uploaded contract (raw text) | **30 days** | Auto-delete (cron job) |
| Extracted clauses | 30 days | Cascade delete with contract |
| LLM prompt runs (audit log) | 30 days | Auto-delete |
| User account | Until user deletes | Immediate on request |

### 2.3 What we never do
- ❌ Never send contract text to any LLM for training
- ❌ Never share contract data with third parties (beyond processors)

---

## 3. Failure modes

Every AI system fails. The question is whether failure is **safe**.

| # | Failure mode | Impact if unmitigated | Mitigation | Where implemented |
|---|---|---|---|---|
| 1 | **Wrong clause type** | User misses critical clause | Review queue for confidence < 0.7 | W12, W13 |
| 2 | **Missed clause** | User signs unaware | Recall metric in eval; negative-case testing | W23 |
| 3 | **Hallucinated quote** | User trusts fake text | Exact substring verification; failed quotes → review | W12 |
| 4 | **Prompt injection** | Model ignores actual task | Delimiter wrapping; system prompt instruction | W12 |
| 5 | **PII leakage in logs** | GDPR violation; PII exposure | Structured logging with redaction filter | W12 |
| 6 | **Provider outage** | No extraction available | Fallback provider (Groq); retry with backoff | W16 |
| 7 | **Context overflow** | Truncation; missing clauses | Guard rejects large contracts; chunking deferred | W8, W21 |
| 8 | **Over-reliance** | User treats extraction as legal review | Disclaimer on every result page; "not legal advice" | W13 |

> **Design principle:** The system never says "sign this." It shows what was found, with citations, and requires human decision. Failure is bounded by human-in-the-loop.

---

## 4. Human-in-the-loop

### 4.1 What the human does
- **Reviews** every clause flagged by the system
- **Accepts, rejects, or edits** extracted clauses
- **Makes the final decision** about signing, negotiating, or seeking legal advice
- **Never auto-approves** — no exception, even at 100% confidence

### 4.2 What the system does NOT do
- ❌ Never auto-approves a clause based on confidence score
- ❌ Never says "this contract is safe" or "sign this"
- ❌ Never interprets clause meaning (only extracts text)
- ❌ Never provides legal advice

### 4.3 Review queue rules
A clause enters the review queue when **any** of:
- `confidence < 0.7`
- `quote` not verified as exact substring
- `clause_type == "none"` with low confidence

---

## 5. Bias & limitations

### 5.1 Data bias
- **CUAD is US commercial contracts.** German, UK, and other jurisdictions may have different clause patterns. ClauseDesk explicitly scoped to English US contracts in v1.
- **English only.** Non-native English contracts (common for German freelancers with international clients) may extract less reliably.

### 5.2 Scope limitations
- **8 of 41 CUAD clause types covered in v1.** 33 types not extracted — user must read those manually.
- **No interpretation.** System does not flag "unusual" or "risky" clauses. Only extracts what is present.

### 5.3 Over-reliance risk
The biggest ethical risk is **the user treating ClauseDesk as a substitute for legal review**. Mitigations:
- Disclaimer on every page: "This tool extracts clauses. It does not evaluate them."
- Review queue forces human engagement — user cannot skip reading.

---

## 6. Regulatory context

### 6.1 EU AI Act classification
**ClauseDesk is a limited-risk AI system** under the EU AI Act.
- **Not high-risk** (Annex III): does not make decisions affecting access to credit, employment, education, essential services, or migration. Only extracts text; human decides.
- **Not prohibited** (Art. 5): no manipulation, no social scoring, no biometric categorization.
- **Limited-risk obligations** (Art. 50, transparency): Users must be informed they're interacting with AI; AI-generated output must be identifiable.

### 6.2 GDPR compliance
- **Legal basis**: Art. 6(1)(b) — contract performance (extraction service requested by user)
- **Data subject rights**: access, erasure, portability — implemented via API endpoints (W18)
- **Cross-border transfers**: OpenAI (US) — SCCs + user consent required; disclosed in privacy notice.

---

## 7. Ethical design principles (summary)

1. **LLM reads. Code verifies. Human decides.**
2. **Never say "sign this."** Provide evidence, not advice.
3. **Always show citations.** Every claim traceable to source.
4. **No auto-approval.** Human review is mandatory, not optional.
5. **Failure is bounded.** Confidence gates, verification checks, and review queue prevent silent errors.
6. **Data minimization.** Send only what's needed; retain only for the stated period.
7. **Transparency.** Users know AI is used, know what it does and doesn't do.
8. **Scope honestly.** US English contracts, 8 clause types, extraction not interpretation.
