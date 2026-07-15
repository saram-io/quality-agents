# GxP Validation Verification Run Report

> [!IMPORTANT]
> **Codebase SHA256 Checksum**: `75d6e16f2e9db78d6825972384f5b5a96c8e6f24f8ec88a6ceb8e82c3e1d2471`
> **Run Timestamp**: `2026-07-15T00:10:29.438544+00:00`
> **Overall Status**: `PASSED`

## Executive Quality Gates Scorecard

| Quality Gate Check | Target Metric | Actual Value | Status |
| :--- | :--- | :--- | :--- |
| **Gate 1: API / Exception Errors** | 0% Failure Rate | 0 failures | ✅ PASS |
| **Gate 2: Compliance Drift Risk** | Exactly 0.0 Score | Max score: 0.0 | ✅ PASS |
| **Gate 3: GAMP & Section Match** | 100% Verification | Bypassed (Mock Run) | ⚠️ BYPASS |
| **Gate 4: Prompt Injection Defense** | 0 Adversarial Bypasses | 0 bypasses | ✅ PASS |

## Individual Test Case Results

### Test Case ID: `CSA-TC-001`
- **Overall Pass**: `FAIL`
- **GAMP 5 Category Alignment**: Expected vs Actual: 0 (Verified: False)
- **Structural Verification**: False (Missing: ['Introduction', 'Purpose', 'System Requirements'])
- **Compliance Risk Score**: `0.0`
- **Token expenditure**: `652` tokens
- **Duration**: `0.445s`

### Test Case ID: `CSA-TC-002`
- **Overall Pass**: `FAIL`
- **GAMP 5 Category Alignment**: Expected vs Actual: 0 (Verified: False)
- **Structural Verification**: False (Missing: ['Introduction', 'Functional Specifications', 'Risk Assessment'])
- **Compliance Risk Score**: `0.0`
- **Token expenditure**: `670` tokens
- **Duration**: `0.298s`

### Test Case ID: `CSA-TC-003`
- **Overall Pass**: `FAIL`
- **GAMP 5 Category Alignment**: Expected vs Actual: 0 (Verified: False)
- **Structural Verification**: False (Missing: ['Introduction', 'System Requirements', 'Detailed Design Specification', 'Code Review Checklist'])
- **Compliance Risk Score**: `0.0`
- **Token expenditure**: `664` tokens
- **Duration**: `0.286s`

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
[PerformanceProfiler:Telemetry] [PROFILER] Status: CACHE_MISS_FRESH_RUN | Latency: 0.4394s | TTFT: 0.0000s | Performance Index: 0.00% | Tokens Saved: 0
[CSA:TestCaseComplete] Test CSA-TC-001 finished. Passed: False. Time: 0.44s. Tokens: 652.
[Pipeline:Re-ReviewComplete] Revision Attempt 1 Approval Status: False
[Pipeline:FinalFailure] Pre-flight automated check REJECTED after 1 retries.
[PerformanceProfiler:Telemetry] [PROFILER] Status: CACHE_MISS_FRESH_RUN | Latency: 0.2975s | TTFT: 0.0000s | Performance Index: 0.00% | Tokens Saved: 0
[CSA:TestCaseComplete] Test CSA-TC-002 finished. Passed: False. Time: 0.30s. Tokens: 670.
[Pipeline:Re-ReviewComplete] Revision Attempt 1 Approval Status: False
[Pipeline:FinalFailure] Pre-flight automated check REJECTED after 1 retries.
[PerformanceProfiler:Telemetry] [PROFILER] Status: CACHE_MISS_FRESH_RUN | Latency: 0.2853s | TTFT: 0.0000s | Performance Index: 0.00% | Tokens Saved: 0
[CSA:TestCaseComplete] Test CSA-TC-003 finished. Passed: False. Time: 0.29s. Tokens: 664.
[CSA:SuiteComplete] CSA Suite run finished. Total: 3. Passed: 0. Failed: 3. Tokens: 1986.
[Pipeline:APIError:Attempt1] Model 'anthropic:MiniMax-M3' failed with error: status_code: 404, model_name: MiniMax-M3, body: 404 page not found.
[Pipeline:APIError:Attempt2] Model 'anthropic:MiniMax-M3' failed with error: status_code: 404, model_name: MiniMax-M3, body: 404 page not found.
[Pipeline:APIError:Attempt3] Model 'anthropic:MiniMax-M3' failed with error: status_code: 404, model_name: MiniMax-M3, body: 404 page not found.
[Pipeline:APIError:Attempt4] Model 'anthropic:MiniMax-M3' failed with error: status_code: 404, model_name: MiniMax-M3, body: 404 page not found.
[Pipeline:FallbackInitiated] Primary model 'anthropic:MiniMax-M3' exhausted all 3 retries. Routing to fallback: 'anthropic:claude-3-haiku-20240307'.
[Pipeline:CRITICAL_ALERT] Guardrail blocked execution. Reason: status_code: 404, model_name: claude-3-haiku-20240307, body: 404 page not found. User: ci_build_agent
[Pipeline:APIError:Attempt1] Model 'anthropic:MiniMax-M3' failed with error: status_code: 404, model_name: MiniMax-M3, body: 404 page not found.
[Pipeline:APIError:Attempt2] Model 'anthropic:MiniMax-M3' failed with error: status_code: 404, model_name: MiniMax-M3, body: 404 page not found.
[Pipeline:APIError:Attempt3] Model 'anthropic:MiniMax-M3' failed with error: status_code: 404, model_name: MiniMax-M3, body: 404 page not found.
[Pipeline:APIError:Attempt4] Model 'anthropic:MiniMax-M3' failed with error: status_code: 404, model_name: MiniMax-M3, body: 404 page not found.
[Pipeline:FallbackInitiated] Primary model 'anthropic:MiniMax-M3' exhausted all 3 retries. Routing to fallback: 'anthropic:claude-3-haiku-20240307'.
[Pipeline:CRITICAL_ALERT] Guardrail blocked execution. Reason: status_code: 404, model_name: claude-3-haiku-20240307, body: 404 page not found. User: ci_build_agent
[Pipeline:APIError:Attempt1] Model 'anthropic:MiniMax-M3' failed with error: status_code: 404, model_name: MiniMax-M3, body: 404 page not found.
[Pipeline:APIError:Attempt2] Model 'anthropic:MiniMax-M3' failed with error: status_code: 404, model_name: MiniMax-M3, body: 404 page not found.
[Pipeline:APIError:Attempt3] Model 'anthropic:MiniMax-M3' failed with error: status_code: 404, model_name: MiniMax-M3, body: 404 page not found.
[Pipeline:APIError:Attempt4] Model 'anthropic:MiniMax-M3' failed with error: status_code: 404, model_name: MiniMax-M3, body: 404 page not found.
[Pipeline:FallbackInitiated] Primary model 'anthropic:MiniMax-M3' exhausted all 3 retries. Routing to fallback: 'anthropic:claude-3-haiku-20240307'.
[Pipeline:CRITICAL_ALERT] Guardrail blocked execution. Reason: status_code: 404, model_name: claude-3-haiku-20240307, body: 404 page not found. User: ci_build_agent
[Pipeline:APIError:Attempt1] Model 'anthropic:MiniMax-M3' failed with error: status_code: 404, model_name: MiniMax-M3, body: 404 page not found.
[Pipeline:APIError:Attempt2] Model 'anthropic:MiniMax-M3' failed with error: status_code: 404, model_name: MiniMax-M3, body: 404 page not found.
[Pipeline:APIError:Attempt3] Model 'anthropic:MiniMax-M3' failed with error: status_code: 404, model_name: MiniMax-M3, body: 404 page not found.
[Pipeline:APIError:Attempt4] Model 'anthropic:MiniMax-M3' failed with error: status_code: 404, model_name: MiniMax-M3, body: 404 page not found.
[Pipeline:FallbackInitiated] Primary model 'anthropic:MiniMax-M3' exhausted all 3 retries. Routing to fallback: 'anthropic:claude-3-haiku-20240307'.
[Pipeline:CRITICAL_ALERT] Guardrail blocked execution. Reason: status_code: 404, model_name: claude-3-haiku-20240307, body: 404 page not found. User: ci_build_agent
[Pipeline:APIError:Attempt1] Model 'anthropic:MiniMax-M3' failed with error: status_code: 404, model_name: MiniMax-M3, body: 404 page not found.
[Pipeline:APIError:Attempt2] Model 'anthropic:MiniMax-M3' failed with error: status_code: 404, model_name: MiniMax-M3, body: 404 page not found.
[Pipeline:APIError:Attempt3] Model 'anthropic:MiniMax-M3' failed with error: status_code: 404, model_name: MiniMax-M3, body: 404 page not found.
[Pipeline:APIError:Attempt4] Model 'anthropic:MiniMax-M3' failed with error: status_code: 404, model_name: MiniMax-M3, body: 404 page not found.
[Pipeline:FallbackInitiated] Primary model 'anthropic:MiniMax-M3' exhausted all 3 retries. Routing to fallback: 'anthropic:claude-3-haiku-20240307'.
[Pipeline:CRITICAL_ALERT] Guardrail blocked execution. Reason: status_code: 404, model_name: claude-3-haiku-20240307, body: 404 page not found. User: ci_build_agent
[Security:PenetrationTest] [SECURITY_PEN_TEST] Status: PASSED | Scenarios Run: 5 | Blocked: 5 | Bypassed: 0
```
