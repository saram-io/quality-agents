# Multi-Agent CSV Validation Dashboard UI

This is the front-end user interface for the Multi-Agent Computer System Validation (CSV) pipeline, built using **React, TypeScript, Vite, and Tailwind CSS**. 

The dashboard provides real-time oversight of validation document generation, human-in-the-loop signing loops, and audit history, fully compliant with **21 CFR Part 11** and **GAMP 5** software qualification expectations.

---

## Key Features

1. **Agent Execution Control Panel**:
   - Allows quality engineers to enter target system requirements.
   - Monitors multi-agent orchestration logs (Grounding $\rightarrow$ Drafting $\rightarrow$ Review) in real time.
2. **Interactive Drafting Workspace**:
   - Split-screen workspace displaying generated document sections (such as URS, Risk Assessment, or Traceability Matrices) side-by-side with semantic grounding SOP notes and compliance logs.
3. **21 CFR Part 11 Signature Portal**:
   - Restricts document locking to validated email credentials.
   - Enforces electronic signature meaning (e.g. *Validation Review Approval*) and prints a permanent signature record block.
   - Implements a visual **"UNCONTROLLED COPY WHEN PRINTED"** watermark alert across un-signed drafts, replacing it with a **"CONTROLLED GxP RECORD"** banner once signed.

---

## Getting Started

### Prerequisites
- Node.js ($\ge 18.0.0$)
- npm or pnpm

### Installation

Navigate to the `frontend/` directory and install dependencies:
```bash
npm install
```

### Running the Development Server

Start the development server with Hot Module Replacement (HMR) enabled:
```bash
npm run dev
```

The app will be served at `http://localhost:5173`.

---

## Design System and Stack
- **Framework**: Vite + React + TypeScript
- **Styling**: Tailwind CSS
- **Components Style**: shadcn/ui-styled high-contrast grids, badges, tables, and modal drawers.
- **Compliance Visual Boundaries**: Emphasizes drafts as unverified suggestions until human-in-the-loop signing locking events occur.
