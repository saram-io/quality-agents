# GxP Validation Verification Run Report

> [!IMPORTANT]
> **Codebase SHA256 Checksum**: `0edee9120aee1e7e7a3bda28aeb9db1522f915caae688f6e30ac9787a15dd68c`
> **Run Timestamp**: `2026-07-14T23:55:40.878947+00:00`
> **Overall Status**: `PASSED`

## Executive Quality Gates Scorecard

| Quality Gate Check | Target Metric | Actual Value | Status |
| :--- | :--- | :--- | :--- |
| **Gate 1: API / Exception Errors** | 0% Failure Rate | 0 failures | ✅ PASS |
| **Gate 2: Compliance Drift Risk** | Exactly 0.0 Score | Max score: 0.0 | ✅ PASS |
| **Gate 3: GAMP & Section Match** | 100% Verification | Bypassed (Mock Run) | ⚠️ BYPASS |

## Individual Test Case Results

### Test Case ID: `CSA-TC-001`
- **Overall Pass**: `FAIL`
- **GAMP 5 Category Alignment**: Expected vs Actual: 0 (Verified: False)
- **Structural Verification**: False (Missing: ['Introduction', 'Purpose', 'System Requirements'])
- **Compliance Risk Score**: `0.0`
- **Token expenditure**: `652` tokens
- **Duration**: `0.506s`

### Test Case ID: `CSA-TC-002`
- **Overall Pass**: `FAIL`
- **GAMP 5 Category Alignment**: Expected vs Actual: 0 (Verified: False)
- **Structural Verification**: False (Missing: ['Introduction', 'Functional Specifications', 'Risk Assessment'])
- **Compliance Risk Score**: `0.0`
- **Token expenditure**: `670` tokens
- **Duration**: `0.32s`

### Test Case ID: `CSA-TC-003`
- **Overall Pass**: `FAIL`
- **GAMP 5 Category Alignment**: Expected vs Actual: 0 (Verified: False)
- **Structural Verification**: False (Missing: ['Introduction', 'System Requirements', 'Detailed Design Specification', 'Code Review Checklist'])
- **Compliance Risk Score**: `0.0`
- **Token expenditure**: `664` tokens
- **Duration**: `0.305s`

## System Audit Log Trail

```text
[CSA:SuiteStart] Launching CSA automated assurance suite on 3 cases.
[CSA:TestCaseStart] Executing CSA verification test case CSA-TC-001 (A simple non-configured off-the-shelf la...)
[CSA:TestCaseStart] Executing CSA verification test case CSA-TC-002 (A configurable LIMS portal to ingest bat...)
[CSA:TestCaseStart] Executing CSA verification test case CSA-TC-003 (A custom AI batch release engine impleme...)
[GroundingAgent:SOPFetch] User 'ci_build_agent' requested SOP: 'a' for target system 'Batch Ingestion and Automated Release Portal (BIARP)'.
[GroundingAgent:VectorQueryStart] Executing vector query: 'a'.
[GroundingAgent:VectorQueryResults] Retrieved 3 total vector matches. 0 passed confidence threshold >= 0.70.
[GroundingAgent:SOPFetch] User 'ci_build_agent' requested SOP: 'a' for target system 'Batch Ingestion and Automated Release Portal (BIARP)'.
[GroundingAgent:VectorQueryStart] Executing vector query: 'a'.
[GroundingAgent:VectorQueryResults] Retrieved 3 total vector matches. 0 passed confidence threshold >= 0.70.
[GroundingAgent:SOPFetch] User 'ci_build_agent' requested SOP: 'a' for target system 'Batch Ingestion and Automated Release Portal (BIARP)'.
[GroundingAgent:VectorQueryStart] Executing vector query: 'a'.
[GroundingAgent:VectorQueryResults] Retrieved 3 total vector matches. 0 passed confidence threshold >= 0.70.
[Pipeline:GroundingComplete] GAMP Category: 0. Applicable SOPs: ['a']
[Pipeline:DraftingPromptLoaded] Loaded prompt template 'validation_drafting' version: 1.4.2
[Pipeline:GroundingComplete] GAMP Category: 0. Applicable SOPs: ['a']
[Pipeline:DraftingPromptLoaded] Loaded prompt template 'validation_drafting' version: 1.4.2
[Pipeline:GroundingComplete] GAMP Category: 0. Applicable SOPs: ['a']
[Pipeline:DraftingPromptLoaded] Loaded prompt template 'validation_drafting' version: 1.4.2
[Pipeline:DraftingComplete] Document Draft created: a
[Pipeline:RiskScan] Compliance risk score evaluated: 0.0
[Pipeline:DraftingComplete] Document Draft created: a
[Pipeline:RiskScan] Compliance risk score evaluated: 0.0
[Pipeline:DraftingComplete] Document Draft created: a
[Pipeline:RiskScan] Compliance risk score evaluated: 0.0
[Pipeline:ReviewComplete] Approval Status: False
[Pipeline:ReviewComplete] Approval Status: False
[Pipeline:ReviewComplete] Approval Status: False
[Pipeline:RevisionRequired] Review rejected. Gaps: ['a']. Remedial Actions: None. Initiating correction loop (Attempt 1/1).
[Pipeline:RevisionRequired] Review rejected. Gaps: ['a']. Remedial Actions: None. Initiating correction loop (Attempt 1/1).
[Pipeline:RevisionRequired] Review rejected. Gaps: ['a']. Remedial Actions: None. Initiating correction loop (Attempt 1/1).
[Pipeline:Re-RiskScan] Revision Attempt 1 Compliance risk score: 0.0
[Pipeline:Re-RiskScan] Revision Attempt 1 Compliance risk score: 0.0
[Pipeline:Re-RiskScan] Revision Attempt 1 Compliance risk score: 0.0
[Pipeline:Re-ReviewComplete] Revision Attempt 1 Approval Status: False
[Pipeline:FinalFailure] Pre-flight automated check REJECTED after 1 retries.
[PerformanceProfiler:Telemetry] [PROFILER] Status: CACHE_MISS_FRESH_RUN | Latency: 0.5051s | TTFT: 0.0000s | Performance Index: 0.00% | Tokens Saved: 0
[CSA:TestCaseComplete] Test CSA-TC-001 finished. Passed: False. Time: 0.51s. Tokens: 652.
[Pipeline:Re-ReviewComplete] Revision Attempt 1 Approval Status: False
[Pipeline:FinalFailure] Pre-flight automated check REJECTED after 1 retries.
[PerformanceProfiler:Telemetry] [PROFILER] Status: CACHE_MISS_FRESH_RUN | Latency: 0.3195s | TTFT: 0.0000s | Performance Index: 0.00% | Tokens Saved: 0
[CSA:TestCaseComplete] Test CSA-TC-002 finished. Passed: False. Time: 0.32s. Tokens: 670.
[Pipeline:Re-ReviewComplete] Revision Attempt 1 Approval Status: False
[Pipeline:FinalFailure] Pre-flight automated check REJECTED after 1 retries.
[PerformanceProfiler:Telemetry] [PROFILER] Status: CACHE_MISS_FRESH_RUN | Latency: 0.3051s | TTFT: 0.0000s | Performance Index: 0.00% | Tokens Saved: 0
[CSA:TestCaseComplete] Test CSA-TC-003 finished. Passed: False. Time: 0.31s. Tokens: 664.
[CSA:SuiteComplete] CSA Suite run finished. Total: 3. Passed: 0. Failed: 3. Tokens: 1986.
```
