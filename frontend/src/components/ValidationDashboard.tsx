import React, { useState } from "react";
import {
  Shield,
  Lock,
  Unlock,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Database,
  Signature,
  FileCheck,
  Send,
  Loader2,
} from "lucide-react";

// =====================================================================
// TypeScript Interfaces matching our Quality System Schemas
// =====================================================================

interface GroundingAnalysis {
  applicable_sops: string[];
  regulatory_constraints: string[];
  gamp_category: number;
}

interface ValidationDraft {
  document_type: string;
  sections: { [key: string]: string };
  verification_checklist: string[];
  is_draft: boolean;
}

interface ReviewReport {
  approved: boolean;
  validation_gaps: string[];
  remedial_actions_required: string | null;
}

interface AuditLog {
  step: string;
  message: string;
}

// Mock database SOP records for display in the grounding panel
const MOCK_SOP_DB = [
  {
    id: "SOP-1024",
    title: "Validation of Automated Batch Release",
    text: "SOP-1024: All software implementing automated batch release of GxP materials must undergo pre-flight qualification checking. It requires GAMP Category 4 configured software validation, a defined testing checklist, and explicit 21 CFR Part 11 signature gates.",
  },
  {
    id: "SOP-808",
    title: "Quality Risk Controls for Digital Ingestion",
    text: "SOP-808: Digital ingestion of critical batch data requires automated checksum validation, high-speed boundary checks, and real-time failure state alerting to mitigate risks of corrupted batch logs.",
  },
  {
    id: "SOP-202",
    title: "Electronic Records and Signatures",
    text: "SOP-202: Systems must maintain a secure, computer-generated, time-stamped audit trail recording the date, time, and operator action for any modifications. Electronic signatures must be unique to one individual and display the printed name, date/time, and meaning.",
  },
  {
    id: "SOP-101",
    title: "Software Validation Standard",
    text: "SOP-101: Any software deployed in a GxP environment requires a User Requirement Specification (URS). Category 4 configured systems require Functional Specifications (FS) and IQ/OQ testing. Category 5 custom systems require full lifecycle validation.",
  },
];

export default function ValidationDashboard() {
  // App states
  const [activePrompt, setActivePrompt] = useState(
    "Draft a User Requirement Specification (URS) for an automated batch release system with high-speed digital ingestion."
  );
  const [pipelineState, setPipelineState] = useState<
    "idle" | "ingest" | "grounding" | "drafting" | "reviewing" | "ready_for_signature" | "signed"
  >("idle");

  // Simulated metrics
  const [inputTokens, setInputTokens] = useState(0);
  const [outputTokens, setOutputTokens] = useState(0);
  const [totalCost, setTotalCost] = useState(0);
  const [timeElapsed, setTimeElapsed] = useState(0.0);

  // Generated payloads
  const [grounding, setGrounding] = useState<GroundingAnalysis | null>(null);
  const [draft, setDraft] = useState<ValidationDraft | null>(null);
  const [review, setReview] = useState<ReviewReport | null>(null);
  const [riskScore, setRiskScore] = useState(0.0);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);

  // Editor states
  const [editableSections, setEditableSections] = useState<{ [key: string]: string }>({});
  const [selectedSection, setSelectedSection] = useState<string>("");

  // Signature modal states
  const [isSignModalOpen, setIsSignModalOpen] = useState(false);
  const [signerEmail, setSignerEmail] = useState("quality_director_clara@biopharma.com");
  const [signerPin, setSignerPin] = useState("");
  const [signatureMeaning, setSignatureMeaning] = useState("Review and Approval of Content");
  const [signedStamp, setSignedStamp] = useState<{
    signer: string;
    timestamp: string;
    meaning: string;
    hash: string;
  } | null>(null);

  // active tab in context window
  const [contextTab, setContextTab] = useState<"sops" | "review" | "audit">("sops");

  // Simulate pipeline execution
  const handleTriggerPipeline = () => {
    setPipelineState("ingest");
    setInputTokens(0);
    setOutputTokens(0);
    setTotalCost(0);
    setTimeElapsed(0);
    setGrounding(null);
    setDraft(null);
    setReview(null);
    setRiskScore(0);
    setSignedStamp(null);
    setAuditLogs([{ step: "Pipeline:Start", message: "Executing validation lifecycle pipeline..." }]);

    // Timer
    const startTime = Date.now();
    const interval = setInterval(() => {
      setTimeElapsed(Number(((Date.now() - startTime) / 1000).toFixed(2)));
    }, 100);

    // Timeline simulation
    setTimeout(() => {
      // Step 1: Ingest & Grounding
      setPipelineState("grounding");
      setInputTokens(520);
      setOutputTokens(150);
      setTotalCost(0.012);
      setGrounding({
        applicable_sops: ["SOP-1024", "SOP-808", "SOP-202"],
        regulatory_constraints: [
          "Secure audit trail logs for digital ingestion",
          "21 CFR Part 11 automated signature constraints",
          "GAMP 5 Category 4 system qualification",
        ],
        gamp_category: 4,
      });
      setAuditLogs((prev) => [
        ...prev,
        {
          step: "GroundingAgent:SOPFetch",
          message: "Fetched applicable rules for high-speed digital batch release.",
        },
        {
          step: "Pipeline:GroundingComplete",
          message: "Regulatory grounding finished. GAMP Category 4 mapped.",
        },
      ]);
    }, 1200);

    setTimeout(() => {
      // Step 2: Drafting
      setPipelineState("drafting");
      setInputTokens(890);
      setOutputTokens(410);
      setTotalCost(0.024);
      const initialSections = {
        "1. Purpose & Scope":
          "This document specifies the User Requirements for the Batch Ingestion and Automated Release Portal (BIARP). The system is deployed in a GxP environment and must be validated as a GAMP 5 Category 4 system under SOP-1024.",
        "2. Functional Requirements":
          "FR-01: The system shall ingest batch calibration logs from digital scales at high-speeds.\nFR-02: The ingestion interface must run an automated checksum validation on input payloads to check for corrupted logs.\nFR-03: Real-time alerting shall fire upon boundary failure events.",
        "3. 21 CFR Part 11 Constraints":
          "Systems must maintain a secure, computer-generated, time-stamped audit trail tracking all user record changes.\nElectronic signature approval is required prior to releasing any batch calibrations.",
      };
      setDraft({
        document_type: "User Requirement Specification (URS)",
        sections: initialSections,
        verification_checklist: [
          "Verify checksum validations fire on corrupted logs",
          "Verify real-time alerts trigger on ingestion failures",
          "Verify audit trail records user identity and timestamp",
        ],
        is_draft: true,
      });
      setEditableSections(initialSections);
      setSelectedSection("1. Purpose & Scope");
      setRiskScore(0.2); // Low Risk
      setAuditLogs((prev) => [
        ...prev,
        {
          step: "Pipeline:DraftingComplete",
          message: "Draft validation URS document successfully compiled.",
        },
        {
          step: "Pipeline:RiskScan",
          message: "Compliance scan finished. Output risk score: 0.2 (Safe).",
        },
      ]);
    }, 2800);

    setTimeout(() => {
      // Step 3: Pre-flight Quality Audit Review
      setPipelineState("reviewing");
      setInputTokens(1240);
      setOutputTokens(590);
      setTotalCost(0.038);
      setReview({
        approved: true,
        validation_gaps: [],
        remedial_actions_required: null,
      });
      setAuditLogs((prev) => [
        ...prev,
        {
          step: "Pipeline:ReviewComplete",
          message: "Pre-flight check approved. Document is clean.",
        },
        {
          step: "Pipeline:FinalApproval",
          message: "Automated verification completed. Flagged: PENDING_HUMAN_SIGNATURE.",
        },
      ]);
      setPipelineState("ready_for_signature");
      clearInterval(interval);
    }, 4200);
  };

  // Section editor update
  const handleSectionTextChange = (text: string) => {
    if (pipelineState === "signed") return; // Read-only
    setEditableSections((prev) => ({
      ...prev,
      [selectedSection]: text,
    }));

    // Perform real-time compliance checks to calculate risk score
    let newRisk = 0.0;
    const lowerText = text.toLowerCase();
    if (lowerText.includes("self-modifying loop")) newRisk = 1.0;
    else if (lowerText.includes("bypasses human review") || lowerText.includes("bypass human review")) newRisk = 0.9;
    else if (lowerText.includes("unlogged change")) newRisk = 0.8;
    else if (lowerText.includes("delete audit trail") || lowerText.includes("delete audit log")) newRisk = 1.0;
    else if (lowerText.includes("bypass signature")) newRisk = 0.9;

    if (newRisk > 0) {
      setRiskScore(newRisk);
      setReview({
        approved: false,
        validation_gaps: [
          `Detected compliance red flag phrase matching calculated risk: ${newRisk}`,
        ],
        remedial_actions_required: "Resolve the risk flags (e.g. self-modifying loops or bypassed reviews).",
      });
    } else {
      setRiskScore(0.2);
      setReview({
        approved: true,
        validation_gaps: [],
        remedial_actions_required: null,
      });
    }
  };

  // Submit Electronic Signature
  const handleSignConfirm = (e: React.FormEvent) => {
    e.preventDefault();
    if (!signerPin) return;

    // Simulate 21 CFR Part 11 encryption hash generation
    const fakeHash = "SHA256-" + Math.random().toString(36).substring(2, 10).toUpperCase() + "COMPLIANT";

    setSignedStamp({
      signer: signerEmail,
      timestamp: new Date().toISOString().replace("T", " ").substring(0, 19) + " UTC",
      meaning: signatureMeaning,
      hash: fakeHash,
    });

    setPipelineState("signed");
    setIsSignModalOpen(false);

    setAuditLogs((prev) => [
      ...prev,
      {
        step: "Pipeline:SignedAndLocked",
        message: `Validated by ${signerEmail} (${signatureMeaning}). Document locked.`,
      },
    ]);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* 21 CFR Part 11 Top Header Bar */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-6 py-4 flex flex-col sm:flex-row items-center justify-between gap-4 sticky top-0 z-40">
        <div className="flex items-center gap-3">
          <div className="bg-emerald-500/10 p-2 rounded-lg border border-emerald-500/20">
            <Shield className="h-6 w-6 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
              GxP Computer System Validation (CSV) Engine
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 bg-emerald-500/15 text-emerald-400 border border-emerald-500/35 rounded">
                21 CFR Part 11
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Regulatory compliance automation &amp; Computer Software Assurance (CSA) harness
            </p>
          </div>
        </div>

        {/* Token Metrics and telemetry badges */}
        <div className="flex items-center gap-3 bg-slate-950/80 px-4 py-2 rounded-lg border border-slate-800 text-xs font-mono">
          <div className="flex flex-col text-right">
            <span className="text-[10px] text-slate-500 uppercase">Input / Output Tokens</span>
            <span className="text-slate-300">
              {inputTokens} / {outputTokens}
            </span>
          </div>
          <div className="h-6 w-px bg-slate-800"></div>
          <div className="flex flex-col text-right">
            <span className="text-[10px] text-slate-500 uppercase">Run Cost</span>
            <span className="text-emerald-400 font-semibold">
              ${totalCost.toFixed(3)}
            </span>
          </div>
          <div className="h-6 w-px bg-slate-800"></div>
          <div className="flex flex-col text-right">
            <span className="text-[10px] text-slate-500 uppercase">Duration</span>
            <span className="text-slate-300">{timeElapsed.toFixed(1)}s</span>
          </div>
        </div>
      </header>

      {/* Main Layout Area */}
      <main className="flex-1 p-6 grid grid-cols-1 xl:grid-cols-4 gap-6 overflow-hidden">
        {/* Left Side Execution Panel (Timeline Stepper & Prompts) */}
        <section className="xl:col-span-1 flex flex-col gap-6">
          {/* Prompt Entry Box */}
          <div className="bg-slate-900/40 rounded-xl border border-slate-800 p-5 flex flex-col gap-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
              <Cpu className="h-4 w-4 text-emerald-400" />
              <span>Orchestrator Pipeline Prompt</span>
            </div>
            <textarea
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-300 focus:outline-none focus:border-emerald-500 min-h-[100px] resize-none"
              value={activePrompt}
              onChange={(e) => setActivePrompt(e.target.value)}
              disabled={pipelineState !== "idle" && pipelineState !== "ready_for_signature"}
              placeholder="Enter validation requirements..."
            />
            <button
              onClick={handleTriggerPipeline}
              disabled={pipelineState !== "idle" && pipelineState !== "ready_for_signature"}
              className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white font-semibold text-xs py-2.5 rounded-lg flex items-center justify-center gap-2 transition duration-200"
            >
              {pipelineState !== "idle" && pipelineState !== "ready_for_signature" && pipelineState !== "signed" ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin text-emerald-200" />
                  Generating Lifecycle...
                </>
              ) : (
                <>
                  <Send className="h-4.5 w-4.5" />
                  Run Quality Pipeline
                </>
              )}
            </button>
          </div>

          {/* Stepper Monitor (timeline) */}
          <div className="bg-slate-900/40 rounded-xl border border-slate-800 p-5 flex-1 flex flex-col gap-4">
            <div className="text-sm font-semibold text-slate-200 flex items-center justify-between">
              <span>Pipeline Stepper Monitor</span>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 bg-slate-800 border border-slate-700 text-slate-400 rounded">
                Glass Box
              </span>
            </div>

            <div className="flex flex-col gap-5 mt-2 flex-1 justify-around py-4">
              {/* Stepper Step 1 */}
              <div className="flex gap-3 items-start">
                <div className="flex flex-col items-center">
                  <div
                    className={`h-7 w-7 rounded-full border flex items-center justify-center text-xs font-bold ${
                      pipelineState === "idle"
                        ? "bg-slate-950 border-slate-800 text-slate-500"
                        : pipelineState === "ingest"
                        ? "bg-emerald-500/10 border-emerald-500 text-emerald-400 animate-pulse"
                        : "bg-emerald-500 border-emerald-500 text-slate-950"
                    }`}
                  >
                    {pipelineState !== "idle" && pipelineState !== "ingest" ? "✓" : "1"}
                  </div>
                  <div className="w-0.5 h-10 bg-slate-800"></div>
                </div>
                <div className="text-xs">
                  <h3 className="font-semibold text-slate-200">Data Ingest Agent</h3>
                  <p className="text-slate-400">Parsing &amp; normalizing requirements</p>
                  {pipelineState === "ingest" && (
                    <span className="text-[10px] text-emerald-400 animate-pulse">Processing...</span>
                  )}
                </div>
              </div>

              {/* Stepper Step 2 */}
              <div className="flex gap-3 items-start">
                <div className="flex flex-col items-center">
                  <div
                    className={`h-7 w-7 rounded-full border flex items-center justify-center text-xs font-bold ${
                      pipelineState === "idle" || pipelineState === "ingest"
                        ? "bg-slate-950 border-slate-800 text-slate-500"
                        : pipelineState === "grounding"
                        ? "bg-emerald-500/10 border-emerald-500 text-emerald-400 animate-pulse"
                        : "bg-emerald-500 border-emerald-500 text-slate-950"
                    }`}
                  >
                    {pipelineState !== "idle" && pipelineState !== "ingest" && pipelineState !== "grounding"
                      ? "✓"
                      : "2"}
                  </div>
                  <div className="w-0.5 h-10 bg-slate-800"></div>
                </div>
                <div className="text-xs">
                  <h3 className="font-semibold text-slate-200">Regulatory Grounding</h3>
                  <p className="text-slate-400">Consulting database &amp; SOP maps</p>
                  {pipelineState === "grounding" && (
                    <span className="text-[10px] text-emerald-400 animate-pulse">Running SOP query...</span>
                  )}
                </div>
              </div>

              {/* Stepper Step 3 */}
              <div className="flex gap-3 items-start">
                <div className="flex flex-col items-center">
                  <div
                    className={`h-7 w-7 rounded-full border flex items-center justify-center text-xs font-bold ${
                      pipelineState === "idle" || pipelineState === "ingest" || pipelineState === "grounding"
                        ? "bg-slate-950 border-slate-800 text-slate-500"
                        : pipelineState === "drafting"
                        ? "bg-emerald-500/10 border-emerald-500 text-emerald-400 animate-pulse"
                        : "bg-emerald-500 border-emerald-500 text-slate-950"
                    }`}
                  >
                    {pipelineState !== "idle" &&
                    pipelineState !== "ingest" &&
                    pipelineState !== "grounding" &&
                    pipelineState !== "drafting"
                      ? "✓"
                      : "3"}
                  </div>
                  <div className="w-0.5 h-10 bg-slate-800"></div>
                </div>
                <div className="text-xs">
                  <h3 className="font-semibold text-slate-200">Validation Drafting</h3>
                  <p className="text-slate-400">Assembling URS validation document</p>
                  {pipelineState === "drafting" && (
                    <span className="text-[10px] text-emerald-400 animate-pulse">Compiling markdown...</span>
                  )}
                </div>
              </div>

              {/* Stepper Step 4 */}
              <div className="flex gap-3 items-start">
                <div className="flex flex-col items-center">
                  <div
                    className={`h-7 w-7 rounded-full border flex items-center justify-center text-xs font-bold ${
                      pipelineState === "idle" ||
                      pipelineState === "ingest" ||
                      pipelineState === "grounding" ||
                      pipelineState === "drafting"
                        ? "bg-slate-950 border-slate-800 text-slate-500"
                        : pipelineState === "reviewing"
                        ? "bg-emerald-500/10 border-emerald-500 text-emerald-400 animate-pulse"
                        : "bg-emerald-500 border-emerald-500 text-slate-950"
                    }`}
                  >
                    {pipelineState === "ready_for_signature" || pipelineState === "signed" ? "✓" : "4"}
                  </div>
                </div>
                <div className="text-xs">
                  <h3 className="font-semibold text-slate-200">Quality Pre-flight Review</h3>
                  <p className="text-slate-400">Auditing gaps &amp; compliance checks</p>
                  {pipelineState === "reviewing" && (
                    <span className="text-[10px] text-emerald-400 animate-pulse">Scanning drift flags...</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Split Screen Workspace Area */}
        <section className="xl:col-span-3 flex flex-col gap-6 overflow-hidden">
          {/* Main workspace panels */}
          <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-[480px]">
            {/* Left Workspace (The Draft Document Editor) */}
            <div className="bg-slate-900/40 rounded-xl border border-slate-800 flex flex-col overflow-hidden">
              <div className="bg-slate-900/60 border-b border-slate-800 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-4.5 w-4.5 text-emerald-400" />
                  <span className="text-xs font-bold text-slate-200 uppercase">
                    Validation Draft Editor
                  </span>
                </div>
                {/* Draft Badge Gate */}
                <div>
                  {pipelineState === "signed" ? (
                    <span className="inline-flex items-center gap-1 text-[10px] uppercase font-mono px-2.5 py-0.5 bg-emerald-500/15 text-emerald-400 border border-emerald-500/35 rounded-full font-bold">
                      <Lock className="h-3 w-3" /> APPROVED &amp; LOCKED
                    </span>
                  ) : draft ? (
                    <span className="inline-flex items-center gap-1 text-[10px] uppercase font-mono px-2.5 py-0.5 bg-amber-500/15 text-amber-400 border border-amber-500/35 rounded-full font-bold">
                      <Unlock className="h-3 w-3" /> UNVERIFIED DRAFT
                    </span>
                  ) : (
                    <span className="text-[10px] text-slate-500 uppercase font-mono">No Active Draft</span>
                  )}
                </div>
              </div>

              {/* Editor Workspace content */}
              {draft ? (
                <div className="flex-1 flex flex-col p-4 gap-4 overflow-y-auto">
                  {/* Tab list of sections */}
                  <div className="flex gap-2 border-b border-slate-800 pb-2 overflow-x-auto">
                    {Object.keys(editableSections).map((secTitle) => (
                      <button
                        key={secTitle}
                        onClick={() => setSelectedSection(secTitle)}
                        className={`text-xs px-3 py-1.5 rounded-lg whitespace-nowrap border transition duration-200 ${
                          selectedSection === secTitle
                            ? "bg-slate-800 border-slate-700 text-white font-semibold"
                            : "bg-transparent border-transparent text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        {secTitle}
                      </button>
                    ))}
                  </div>

                  {/* Markdown Text Area */}
                  <div className="flex-1 flex flex-col gap-2">
                    <textarea
                      className="flex-1 w-full bg-slate-950 border border-slate-800 rounded-lg p-4 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500 leading-relaxed resize-none min-h-[220px]"
                      value={editableSections[selectedSection] || ""}
                      onChange={(e) => handleSectionTextChange(e.target.value)}
                      disabled={pipelineState === "signed"}
                    />
                  </div>

                  {/* Checklist Section */}
                  <div className="bg-slate-950/60 rounded-lg border border-slate-800 p-3 text-xs">
                    <h4 className="font-semibold text-slate-300 mb-2 uppercase text-[10px] tracking-wider">
                      Verification Test Checklist
                    </h4>
                    <div className="flex flex-col gap-1.5">
                      {draft.verification_checklist.map((check, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-slate-400 font-mono text-[11px]">
                          <input
                            type="checkbox"
                            checked={pipelineState === "signed"}
                            disabled={pipelineState !== "signed"}
                            className="rounded border-slate-700 text-emerald-600 focus:ring-0 focus:ring-offset-0"
                          />
                          <span>{check}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-slate-500 text-xs gap-3">
                  <FileText className="h-10 w-10 text-slate-700" />
                  <span>Execute the validation pipeline to generate a draft.</span>
                </div>
              )}
            </div>

            {/* Right Workspace (Grounding SOP DB, pre-flight review, risk gauges) */}
            <div className="bg-slate-900/40 rounded-xl border border-slate-800 flex flex-col overflow-hidden">
              {/* Tab Selector */}
              <div className="bg-slate-900/60 border-b border-slate-800 px-2 py-1.5 flex items-center justify-between">
                <div className="flex gap-1">
                  <button
                    onClick={() => setContextTab("sops")}
                    className={`text-xs px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition duration-200 ${
                      contextTab === "sops" ? "bg-slate-800 text-white font-semibold" : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <Database className="h-3.5 w-3.5" /> SOP Grounding Context
                  </button>
                  <button
                    onClick={() => setContextTab("review")}
                    className={`text-xs px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition duration-200 ${
                      contextTab === "review" ? "bg-slate-800 text-white font-semibold" : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <FileCheck className="h-3.5 w-3.5" /> Pre-Flight Review
                  </button>
                  <button
                    onClick={() => setContextTab("audit")}
                    className={`text-xs px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition duration-200 ${
                      contextTab === "audit" ? "bg-slate-800 text-white font-semibold" : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <Signature className="h-3.5 w-3.5" /> Audit Logger
                  </button>
                </div>
              </div>

              {/* Tab Workspace content */}
              <div className="flex-1 p-4 overflow-y-auto">
                {contextTab === "sops" && (
                  <div className="flex flex-col gap-4">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                      <span className="text-xs font-semibold text-slate-300 uppercase text-[10px]">
                        GxP SOP Database Excerpts
                      </span>
                      {grounding && (
                        <span className="text-[10px] text-slate-500 font-mono">
                          Matched Category {grounding.gamp_category} System
                        </span>
                      )}
                    </div>
                    {grounding ? (
                      <div className="flex flex-col gap-3">
                        {/* SOP matches list */}
                        {MOCK_SOP_DB.filter((sop) => grounding.applicable_sops.includes(sop.id)).map((sop) => (
                          <div
                            key={sop.id}
                            className="bg-slate-950/60 rounded-lg border border-slate-800 p-3 hover:border-slate-700 transition duration-200"
                          >
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs font-bold text-white font-mono">{sop.id}</span>
                              <span className="text-[10px] text-slate-400 font-semibold">{sop.title}</span>
                            </div>
                            <p className="text-[11px] text-slate-400 leading-relaxed leading-normal mt-1 text-slate-350">
                              {sop.text}
                            </p>
                          </div>
                        ))}

                        {/* Regulatory constraints list */}
                        <div className="bg-slate-950/40 rounded-lg border border-slate-800/80 p-3 mt-1">
                          <h4 className="text-[10px] uppercase font-bold text-slate-300 mb-2 font-mono tracking-wide">
                            Extracted Regulatory Constraints
                          </h4>
                          <ul className="list-disc list-inside text-[11px] text-slate-400 flex flex-col gap-1.5">
                            {grounding.regulatory_constraints.map((rule, idx) => (
                              <li key={idx} className="leading-relaxed">
                                {rule}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center text-slate-500 text-xs py-20 gap-3">
                        <Database className="h-8 w-8 text-slate-700" />
                        <span>Grounding analysis results will appear here.</span>
                      </div>
                    )}
                  </div>
                )}

                {contextTab === "review" && (
                  <div className="flex flex-col gap-4">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                      <span className="text-xs font-semibold text-slate-300 uppercase text-[10px]">
                        Quality Review Report Card
                      </span>
                      {draft && (
                        <span className="flex items-center gap-1.5 text-[11px] font-mono font-semibold">
                          Risk Score:
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] ${
                              riskScore >= 0.8
                                ? "bg-red-500/10 text-red-400 border border-red-500/30"
                                : riskScore >= 0.5
                                ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                                : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                            }`}
                          >
                            {riskScore.toFixed(1)}
                          </span>
                        </span>
                      )}
                    </div>

                    {review ? (
                      <div className="flex flex-col gap-4">
                        {/* Risk scanner meter card */}
                        <div className="bg-slate-950/60 rounded-lg border border-slate-800 p-4">
                          <h4 className="text-[10px] uppercase font-bold text-slate-300 mb-2 tracking-wider">
                            Compliance Drift Guardrail Scan
                          </h4>
                          <div className="w-full bg-slate-900 rounded-full h-2.5 mt-2 border border-slate-800">
                            <div
                              className={`h-2.5 rounded-full transition-all duration-300 ${
                                riskScore >= 0.8
                                  ? "bg-red-500"
                                  : riskScore >= 0.5
                                  ? "bg-amber-500"
                                  : "bg-emerald-500"
                              }`}
                              style={{ width: `${riskScore * 100}%` }}
                            ></div>
                          </div>
                          <p className="text-[11px] text-slate-400 mt-2">
                            {riskScore >= 0.5
                              ? "CRITICAL ALERT: Banned compliance phrases identified. Document contains unsafe non-deterministic statements."
                              : "STATUS SAFE: Document compliant. No non-deterministic phrases identified."}
                          </p>
                        </div>

                        {/* Approval status banner */}
                        <div
                          className={`rounded-lg border p-4 flex items-start gap-3 ${
                            review.approved
                              ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                              : "bg-red-500/10 border-red-500/20 text-red-400"
                          }`}
                        >
                          {review.approved ? (
                            <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
                          ) : (
                            <AlertTriangle className="h-5 w-5 text-red-400 shrink-0 mt-0.5" />
                          )}
                          <div className="text-xs">
                            <h4 className="font-bold text-white uppercase text-[11px]">
                              {review.approved ? "Verification Passed" : "Verification Failed"}
                            </h4>
                            <p className="mt-1 text-slate-300">
                              {review.approved
                                ? "This document satisfies the pre-flight checks and GxP requirements. It is ready for human electronic signature."
                                : "Compliance gaps were identified by the quality audit agent. The document must be revised."}
                            </p>
                          </div>
                        </div>

                        {/* Gaps / Remedial actions list */}
                        {!review.approved && (
                          <div className="bg-slate-950/60 rounded-lg border border-red-500/20 p-3">
                            <h4 className="text-[10px] font-bold text-red-400 uppercase tracking-wide mb-2 font-mono">
                              Compliance Gaps Found
                            </h4>
                            <ul className="list-disc list-inside text-[11px] text-slate-400 flex flex-col gap-1.5">
                              {review.validation_gaps.map((gap, idx) => (
                                <li key={idx}>{gap}</li>
                              ))}
                            </ul>
                            <div className="mt-3 border-t border-slate-800 pt-2 text-[11px]">
                              <span className="font-bold text-white">Remedial Action Required:</span>
                              <p className="text-slate-400 mt-0.5">{review.remedial_actions_required}</p>
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center text-slate-500 text-xs py-20 gap-3">
                        <FileCheck className="h-8 w-8 text-slate-700" />
                        <span>Pre-flight review scorecard will appear here.</span>
                      </div>
                    )}
                  </div>
                )}

                {contextTab === "audit" && (
                  <div className="flex flex-col gap-3">
                    <div className="border-b border-slate-800 pb-2">
                      <span className="text-xs font-semibold text-slate-300 uppercase text-[10px]">
                        Pre-flight Pipeline Logs
                      </span>
                    </div>
                    {auditLogs.length > 0 ? (
                      <div className="flex flex-col gap-2.5 font-mono text-[10px] text-slate-400">
                        {auditLogs.map((log, idx) => (
                          <div key={idx} className="bg-slate-950/40 rounded border border-slate-800/80 p-2 flex flex-col gap-1">
                            <div className="flex items-center justify-between text-slate-300 font-semibold border-b border-slate-900 pb-1">
                              <span>[{log.step}]</span>
                              <span className="text-slate-500">{new Date().toISOString().substring(11, 19)}</span>
                            </div>
                            <span className="text-slate-400 leading-relaxed mt-0.5">{log.message}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center text-slate-500 text-xs py-20 gap-3">
                        <Signature className="h-8 w-8 text-slate-700" />
                        <span>Pipeline execution audit logs will appear here.</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Bottom Human-in-the-Loop Validation Gate Card */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="bg-amber-500/10 p-2 rounded-lg border border-amber-500/20 shrink-0">
                <Signature className="h-6 w-6 text-amber-400" />
              </div>
              <div className="text-xs">
                <h4 className="font-bold text-white uppercase text-[11px] tracking-wider">
                  21 CFR Part 11 Electronic Signature Approval Gate
                </h4>
                <p className="text-slate-400 mt-1 max-w-xl">
                  Non-deterministic AI validation drafts require manual, human-in-the-loop electronic sign-off.
                  Signing locks the document sections and issues a verified GxP compliance certificate stamp.
                </p>
              </div>
            </div>

            <div>
              {pipelineState === "signed" ? (
                <div className="flex items-center gap-2 text-emerald-400 font-bold bg-emerald-500/10 border border-emerald-500/20 px-4 py-2 rounded-lg text-xs font-mono">
                  <CheckCircle2 className="h-4 w-4" /> COMPLIANCE SEAL RECORDED
                </div>
              ) : pipelineState === "ready_for_signature" && review?.approved ? (
                <button
                  onClick={() => setIsSignModalOpen(true)}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs py-2.5 px-5 rounded-lg flex items-center gap-2 transition duration-200 shadow-md shadow-emerald-900/20"
                >
                  <Signature className="h-4 w-4" /> Approve &amp; Electronically Sign
                </button>
              ) : (
                <button
                  disabled
                  className="bg-slate-800 text-slate-500 border border-slate-700/50 font-bold text-xs py-2.5 px-5 rounded-lg flex items-center gap-2 cursor-not-allowed"
                >
                  <Lock className="h-4 w-4" /> Signature Locked
                </button>
              )}
            </div>
          </div>

          {/* Locked Verified GxP Compliance Seal Stamp */}
          {pipelineState === "signed" && signedStamp && (
            <div className="bg-emerald-500/5 border-2 border-dashed border-emerald-500/20 rounded-xl p-5 flex flex-col md:flex-row items-center justify-between gap-6 relative overflow-hidden">
              <div className="absolute right-0 top-0 opacity-[0.03] scale-150 rotate-12 shrink-0">
                <Shield className="h-40 w-40 text-emerald-500" />
              </div>
              <div className="flex items-start gap-4">
                <div className="bg-emerald-500/10 p-2.5 rounded-full border border-emerald-500/30 shrink-0">
                  <FileCheck className="h-7 w-7 text-emerald-400" />
                </div>
                <div className="text-xs">
                  <h4 className="font-bold text-white uppercase text-[11px] tracking-widest text-emerald-400">
                    GxP Validated Compliance Certificate
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1.5 mt-2 font-mono text-slate-350">
                    <span>
                      <strong className="text-slate-400">Signer Email:</strong> {signedStamp.signer}
                    </span>
                    <span>
                      <strong className="text-slate-400">Timestamp:</strong> {signedStamp.timestamp}
                    </span>
                    <span>
                      <strong className="text-slate-400">Meaning of Signature:</strong> {signedStamp.meaning}
                    </span>
                    <span>
                      <strong className="text-slate-400">Signature Hash:</strong> {signedStamp.hash}
                    </span>
                  </div>
                </div>
              </div>
              <div className="text-center shrink-0 border border-emerald-500/20 bg-emerald-500/10 rounded-lg px-4 py-2 font-mono">
                <span className="text-[10px] text-emerald-400 uppercase tracking-widest">Compliance Seal</span>
                <div className="text-sm font-bold text-white uppercase tracking-tight mt-0.5">VALIDATED &amp; LOCKED</div>
              </div>
            </div>
          )}
        </section>
      </main>

      {/* 21 CFR Part 11 Electronic Signature Dialog Modal */}
      {isSignModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 flex flex-col gap-4 shadow-2xl">
            <div className="flex items-center gap-2.5 border-b border-slate-800 pb-3">
              <Signature className="h-5 w-5 text-emerald-400" />
              <h3 className="font-bold text-white text-sm uppercase">21 CFR Part 11 Electronic Sign-off</h3>
            </div>

            <form onSubmit={handleSignConfirm} className="flex flex-col gap-4 text-xs">
              {/* User Email */}
              <div className="flex flex-col gap-1.5">
                <label className="font-semibold text-slate-300">Signer Identity / Email</label>
                <input
                  type="email"
                  required
                  value={signerEmail}
                  onChange={(e) => setSignerEmail(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>

              {/* Password / Pin */}
              <div className="flex flex-col gap-1.5">
                <label className="font-semibold text-slate-300">Password or Pin (21 CFR Dual Auth Key)</label>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={signerPin}
                  onChange={(e) => setSignerPin(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500 font-mono tracking-widest"
                />
              </div>

              {/* Meaning dropdown */}
              <div className="flex flex-col gap-1.5">
                <label className="font-semibold text-slate-300">Meaning of Signature</label>
                <select
                  value={signatureMeaning}
                  onChange={(e) => setSignatureMeaning(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500"
                >
                  <option value="Review and Approval of Content">Review and Approval of Content</option>
                  <option value="Authoring Document">Authoring Document</option>
                  <option value="Quality Assurance Sign-off">Quality Assurance Sign-off</option>
                  <option value="Technical Review Certification">Technical Review Certification</option>
                </select>
              </div>

              {/* Legal GxP Warning */}
              <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 text-[11px] text-slate-300 leading-normal flex gap-2">
                <AlertTriangle className="h-4.5 w-4.5 text-amber-400 shrink-0 mt-0.5" />
                <p>
                  <strong>Compliance Warning Notice:</strong> By entering my password/pin and clicking Sign, I agree
                  that this electronic signature is the legally binding equivalent of my handwritten signature under
                  21 CFR Part 11 and company standards.
                </p>
              </div>

              {/* Modal buttons */}
              <div className="flex gap-3 justify-end mt-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsSignModalOpen(false)}
                  className="bg-transparent hover:bg-slate-800 border border-slate-700 text-slate-300 font-semibold py-2 px-4 rounded-lg transition duration-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!signerPin}
                  className="bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-850 disabled:text-slate-500 disabled:border-slate-800 text-white font-semibold py-2 px-4 rounded-lg flex items-center gap-1.5 transition duration-200"
                >
                  <Signature className="h-4 w-4" /> Sign Document
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
