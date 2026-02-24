An autonomous AI agent system that performs comprehensive code reviews on GitHub Pull Requests using a Parallel Swarm pattern with Decision Engine. Built with Google ADK, Gemini 2.0 Flash, FastAPI, and PyGithub.

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture & Design Pattern](#architecture--design-pattern)
- [System Flowcharts](#system-flowcharts)
- [Component Deep Dive](#component-deep-dive)
- [Agent Specifications](#agent-specifications)
- [Implementation Details](#implementation-details)
- [API & Class Reference](#api--class-reference)
- [GitHub Integration](#github-integration)
- [How to Run](#how-to-run)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)


---

## Project Overview

Code reviews are critical for maintaining code quality, security, and team standards. However, manual reviews are time-consuming, inconsistent across reviewers, and can become bottlenecks in fast-paced development cycles.

This system automates the code review process end-to-end using a **parallel multi-agent AI pipeline** that:

1. **Listens for PR events** via GitHub webhooks (`opened`, `synchronized`, `reopened`)
2. **Fetches the PR diff** (changed lines of code)
3. **Dispatches to 5 specialized review agents in parallel**:
- **Security Auditor** — Detects vulnerabilities, hardcoded secrets, injection risks
- **Style Checker** — Enforces formatting, naming conventions, readability
- **Performance Analyzer** — Identifies bottlenecks, inefficiencies, resource leaks
- **Logic Verifier** — Checks correctness, edge cases, potential bugs
- **Documentation Reviewer** — Ensures comments, docstrings, and explanations exist
4. **Aggregates findings** through a Decision Engine that applies strict logic rules
5. **Posts comprehensive feedback** as a PR comment with file/line-specific fixes
6. **Sets GitHub Status Checks** to physically block or allow merging based on severity

### Key Features

- **Zero-latency parallel execution** — All 5 agents analyze simultaneously
- **Structured output enforcement** — Agents return File | Line | Issue | Fix format
- **Severity-based blocking** — Security failures block merges; style issues don't
- **Non-blocking webhook handling** — Background tasks prevent GitHub timeouts
- **Status check integration** — Visual pass/fail indicators on GitHub UI
- **Language-agnostic** — Works with Python, JavaScript, TypeScript, Go, etc.


---

## Architecture & Design Pattern

**Pattern**: Event-Driven Parallel Swarm with Decision Engine

The system is structured around three layers:

### 1. Event Listener Layer

**FastAPI Webhook Server** ([server.py](https://markdown-confluence.herokuapp.com/md-editor?action=edit&xdm_e=https%3A%2F%2Fprocaltech.atlassian.net&xdm_c=channel-Narva.Apps.Markdown__md-editor&cp=%2Fwiki&xdm_deprecated_addon_key_do_not_use=Narva.Apps.Markdown&lic=none&userAccess=true&cv=1000.0.0-228febe09c7d&jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI3MTIwMjA6YmViYTdjMWItYzBiMy00OTUyLWFkYjktNjUyNTlhODdkZTJlIiwicXNoIjoiZDcwYmMzNDAyOWUyNTM2ZDk2ZjRmODk3MWMzYzgyYmZmN2VkYjRiNWJmNjQ5ODYyNzM4ODNkNWIzMGUxZDQ3ZSIsImlzcyI6IjZmNDZlMmY3LTQ5MDctMzI3Zi05MzUxLWRhNjZiMTljMGE0NCIsImNvbnRleHQiOnt9LCJleHAiOjE3NzE4NDMxODEsImlhdCI6MTc3MTg0MzAwMX0.VHHfEtiuyJCsrMjFoHCbCxPQRyP2X08v-SlXTgcSK0I#))

- Receives `POST /webhook` events from GitHub
- Validates event type and PR action
- Immediately queues review as a `BackgroundTask` and returns 202 to prevent GitHub timeout
- Logs detailed PR metadata (author, files changed, additions/deletions)

### 2. GitHub Integration Layer

**GitHubService** ([github_service.py](https://markdown-confluence.herokuapp.com/md-editor?action=edit&xdm_e=https%3A%2F%2Fprocaltech.atlassian.net&xdm_c=channel-Narva.Apps.Markdown__md-editor&cp=%2Fwiki&xdm_deprecated_addon_key_do_not_use=Narva.Apps.Markdown&lic=none&userAccess=true&cv=1000.0.0-228febe09c7d&jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI3MTIwMjA6YmViYTdjMWItYzBiMy00OTUyLWFkYjktNjUyNTlhODdkZTJlIiwicXNoIjoiZDcwYmMzNDAyOWUyNTM2ZDk2ZjRmODk3MWMzYzgyYmZmN2VkYjRiNWJmNjQ5ODYyNzM4ODNkNWIzMGUxZDQ3ZSIsImlzcyI6IjZmNDZlMmY3LTQ5MDctMzI3Zi05MzUxLWRhNjZiMTljMGE0NCIsImNvbnRleHQiOnt9LCJleHAiOjE3NzE4NDMxODEsImlhdCI6MTc3MTg0MzAwMX0.VHHfEtiuyJCsrMjFoHCbCxPQRyP2X08v-SlXTgcSK0I#))

- Authenticates via `GITHUB_TOKEN` using PyGithub SDK
- Fetches PR metadata (title, files, stats, labels, reviewers)
- Retrieves raw unified diff via GitHub API
- Posts comments to PR as the AI bot
- Sets commit status checks (pending → success/failure) for each review category

### 3. AI Pipeline Layer (Google ADK)

**Three-tier agent hierarchy**:

``` 
root_agent (SequentialAgent)
 └── parallel_review_swarm (ParallelAgent)
      ├── security_auditor (LlmAgent)
      ├── style_checker (LlmAgent)
      ├── performance_analyzer (LlmAgent)
      ├── logic_verifier (LlmAgent)
      └── docs_reviewer (LlmAgent)
 └── review_synthesizer (LlmAgent) ← Decision Engine
```

**Execution Flow**:

1. `parallel_review_swarm` fans out to 5 sub-agents simultaneously
2. Each agent reads the same diff but focuses on its specialty
3. All agents return markdown reports in File | Line | Issue | Fix format
4. `review_synthesizer` receives all 5 reports and applies decision rules:
- **High-severity security issue** → `REQUEST_CHANGES` (blocks merge)
- **Logic/correctness failure** → `REQUEST_CHANGES`
- **Only style/docs issues** → `COMMENT` (doesn't block)
- **No issues** → `APPROVE`
5. Synthesizer outputs structured JSON with final decision, summary markdown, and per-category status


---

## System Flowcharts

### 1. System Architecture Overview

``` 
┌─────────────────────────────────────────────────────────────────────┐
│                           GitHub Repository                          │
│                  (Developer pushes commit to PR)                     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ Webhook Event (pull_request)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Webhook Server                          │
│                         (server.py)                                  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  POST /webhook                                               │   │
│  │  - Validate event type                                       │   │
│  │  - Extract repo, PR#, commit SHA                             │   │
│  │  - Queue background task: process_pr_review()                │   │
│  │  - Return 202 Accepted immediately                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        GitHub Service Layer                          │
│                     (github_service.py)                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  1. Set status checks to "pending"                           │   │
│  │  2. Fetch PR metadata (title, author, files)                 │   │
│  │  3. Fetch raw unified diff                                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ diff_text
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Google ADK Agent Pipeline                         │
│                         (agent.py)                                   │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │         Parallel Review Swarm (ParallelAgent)              │    │
│  │                                                             │    │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │    │
│  │   │  Security   │  │   Style     │  │ Performance │ ...  │    │
│  │   │  Auditor    │  │  Checker    │  │  Analyzer   │      │    │
│  │   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │    │
│  │          │                 │                 │             │    │
│  │          └─────────────────┴─────────────────┘             │    │
│  │                            │                                │    │
│  │                   5 markdown reports                        │    │
│  └────────────────────────────┼────────────────────────────────┘    │
│                               ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │      Review Synthesizer (LlmAgent - Decision Engine)       │    │
│  │                                                             │    │
│  │  - Aggregate all reports                                   │    │
│  │  - Apply decision rules (security fail → block)            │    │
│  │  - Generate unified summary markdown                       │    │
│  │  - Output JSON: {decision, summary_markdown, checks}       │    │
│  └────────────────────────────┬───────────────────────────────┘    │
└────────────────────────────────┼────────────────────────────────────┘
                                 │ {decision, summary, checks}
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GitHub Service Layer (Write)                      │
│                                                                       │
│  1. Post comment on PR with summary_markdown                         │
│  2. Set status checks per category (security, style, etc.)           │
│  3. Set overall-decision status (success/failure)                    │
│                                                                       │
│  If decision == "REQUEST_CHANGES" → Merge button blocked ❌          │
│  If decision == "APPROVE" → Merge button enabled ✅                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. End-to-End Process Flow

``` 
┌─────────────────────────────────────────────────────────────────────┐
│                  Developer pushes code to PR                         │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
              GitHub triggers webhook event
                           │
                           ▼
        ┌─────────────────────────────────────┐
        │    Webhook received by FastAPI      │
        │  (POST /webhook with PR payload)    │
        └──────────────┬──────────────────────┘
                       │
                       ▼
           ┌───────────────────────────┐
           │  Is event type PR-related? │
           └───────┬─────────┬─────────┘
                   │         │
                  No        Yes
                   │         │
                   ▼         ▼
           Return 200   Extract metadata
           (ignored)    (repo, PR#, SHA)
                            │
                            ▼
                  Queue background task
                 (process_pr_review)
                            │
                            ▼
                  Return 202 to GitHub
                   (prevents timeout)
                            │
           ┌────────────────┴────────────────┐
           │   Background Task Execution     │
           └────────────────┬────────────────┘
                            │
                            ▼
              Set status checks → "pending"
                            │
                            ▼
                 Fetch PR diff from GitHub
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  Create ADK session for this PR       │
        │  (session_id = repo_prnum_uuid)       │
        └───────────────┬───────────────────────┘
                        │
                        ▼
            Construct agent_input JSON
            {repo, pr_number, language, diff}
                        │
                        ▼
        ┌───────────────────────────────────────┐
        │   Run root_agent via runner.run_async │
        └───────────────┬───────────────────────┘
                        │
                        ▼
        ┌────────────────────────────────────────┐
        │   Step 1: parallel_review_swarm        │
        │   launches 5 agents simultaneously     │
        │                                         │
        │   [security_auditor]                   │
        │   [style_checker]                      │
        │   [performance_analyzer]               │
        │   [logic_verifier]                     │
        │   [docs_reviewer]                      │
        │                                         │
        │   All agents analyze diff in parallel  │
        └────────────────┬───────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────────┐
        │   Step 2: review_synthesizer           │
        │   (Decision Engine)                    │
        │                                         │
        │   Input: 5 markdown reports            │
        │   Process: Apply decision rules        │
        │   Output: JSON with decision & checks  │
        └────────────────┬───────────────────────┘
                         │
                         ▼
              Parse JSON response
          (decision, summary_markdown, checks)
                         │
                         ▼
           Post comment on GitHub PR
        (summary_markdown with fixes)
                         │
                         ▼
        Set status checks per category
        (security, style, performance, logic)
                         │
                         ▼
           Set overall-decision status
        (success → unblocks merge button)
        (failure → blocks merge button)
                         │
                         ▼
        ┌─────────────────────────────────────┐
        │      Review complete ✅              │
        │  Developer sees comment & statuses   │
        └─────────────────────────────────────┘
```

### 3. Parallel Agent Pipeline Detail

``` 
┌──────────────────────────────────────────────────────────────────────┐
│                        Input (from server.py)                         │
│                                                                        │
│  {                                                                     │
│    "repo": "owner/repo-name",                                         │
│    "pr_number": 42,                                                   │
│    "language": "python",                                              │
│    "diff": "diff --git a/file.py b/file.py\n+new_code\n-old_code"    │
│  }                                                                     │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    root_agent (SequentialAgent)                       │
│                                                                        │
│  Sub-agents:                                                          │
│    1. parallel_review_swarm                                           │
│    2. review_synthesizer                                              │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│           PHASE 1: Parallel Review Swarm (ParallelAgent)             │
│                                                                        │
│  Receives: agent_input JSON with diff                                │
│  Dispatches to 5 LlmAgents in parallel:                              │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ security_auditor (output_key: "security_report")               │ │
│  │ ─────────────────────────────────────────────────────────────  │ │
│  │ Analyzes: Injection risks, hardcoded secrets, unsafe APIs     │ │
│  │ Output: Markdown with **File:** **Line:** **Issue:** **Fix:**  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ style_checker (output_key: "style_report")                     │ │
│  │ ─────────────────────────────────────────────────────────────  │ │
│  │ Analyzes: Formatting, naming, readability, dead code           │ │
│  │ Output: Markdown with **File:** **Line:** **Issue:** **Fix:**  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ performance_analyzer (output_key: "performance_report")        │ │
│  │ ─────────────────────────────────────────────────────────────  │ │
│  │ Analyzes: Bottlenecks, O(n^2) loops, resource leaks           │ │
│  │ Output: Markdown with **File:** **Line:** **Issue:** **Fix:**  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ logic_verifier (output_key: "logic_report")                    │ │
│  │ ─────────────────────────────────────────────────────────────  │ │
│  │ Analyzes: Correctness, edge cases, potential bugs              │ │
│  │ Output: Markdown with **File:** **Line:** **Issue:** **Fix:**  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ docs_reviewer (output_key: "docs_report")                      │ │
│  │ ─────────────────────────────────────────────────────────────  │ │
│  │ Analyzes: Comments, docstrings, README updates                 │ │
│  │ Output: Markdown with **File:** **Line:** **Issue:** **Fix:**  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  All 5 agents run concurrently (Google ADK handles parallelism)      │
│                                                                        │
│  Output Context (passed to Phase 2):                                 │
│  {                                                                    │
│    "security_report": "markdown...",                                 │
│    "style_report": "markdown...",                                    │
│    "performance_report": "markdown...",                              │
│    "logic_report": "markdown...",                                    │
│    "docs_report": "markdown..."                                      │
│  }                                                                    │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│         PHASE 2: Review Synthesizer (LlmAgent - Decision Engine)     │
│                                                                        │
│  Input: All 5 reports from session context                           │
│                                                                        │
│  Processing:                                                          │
│  1. Read all reports                                                 │
│  2. Apply Decision Rules:                                            │
│     - IF security has HIGH severity → REQUEST_CHANGES                │
│     - IF logic fails → REQUEST_CHANGES                               │
│     - IF only style/docs issues → COMMENT                            │
│     - IF no issues → APPROVE                                         │
│  3. Preserve exact File/Line/Fix blocks from sub-agents              │
│  4. Generate unified markdown summary prioritizing critical issues   │
│                                                                        │
│  Output: JSON                                                         │
│  {                                                                    │
│    "decision": "APPROVE" | "REQUEST_CHANGES" | "COMMENT",            │
│    "summary_markdown": "### Code Review...\n**Security**\n...",      │
│    "checks": {                                                        │
│      "security": "success" | "failure",                              │
│      "style": "success" | "failure",                                 │
│      "performance": "success" | "failure",                           │
│      "logic": "success" | "failure"                                  │
│    }                                                                  │
│  }                                                                    │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   Final Response (to server.py)                       │
│                                                                        │
│  - decision: Used to determine if merge button should be blocked     │
│  - summary_markdown: Posted as PR comment                            │
│  - checks: Used to set GitHub status checks per category             │
└──────────────────────────────────────────────────────────────────────┘
```


---

## Component Deep Dive

### [server.py](http://server.py/)

The FastAPI webhook listener and orchestrator.

#### Key Functions

`validate_environment_variables()`

- Runs on startup before initializing services
- Checks for required env vars: `GITHUB_TOKEN`, `GEMINI_MODEL`, `GOOGLE_API_KEY` (or `GOOGLE_CLOUD_PROJECT` if using VertexAI)
- Exits with detailed error message if any are missing or empty
- Prevents silent failures from missing credentials

`process_pr_review(repo_name, pr_number, commit_sha, language)`

- **Async background task** — runs after webhook returns 202 to GitHub
- Execution steps:
1. Fetch PR metadata via `gh_service.get_pr_metadata()`
2. Set status checks to "pending" for all categories
3. Fetch raw diff via `gh_service.get_pr_diff()`
4. Truncate diff to 50KB if needed (to fit LLM context window)
5. Create isolated ADK session (unique session_id per PR)
6. Construct agent input JSON: `{repo, pr_number, language, diff}`
7. Run `runner.run_async()` and collect final JSON response
8. Strip code fences from response (`json ... `)
9. Parse JSON into `{decision, summary_markdown, checks}` dict
10. Post `summary_markdown` as PR comment
11. Set status checks per category (security, style, etc.) based on `checks` dict
12. Set overall-decision status (success if APPROVE, failure if REQUEST_CHANGES)
- Error handling: Catches all exceptions and sets "error" status on commit

`@app.post("/webhook")`

- Receives GitHub webhook POST requests
- Validates `X-GitHub-Event` header (only processes `pull_request` events)
- Filters PR actions (only processes `opened`, `synchronize`, `reopened`)
- Extracts: repo name, PR number, commit SHA, PR title, author, branches
- Logs detailed PR information (title, author, branches, URL, files changed)
- Queues `process_pr_review()` as a `BackgroundTask`
- Returns `{"message": "Review queued"}` immediately (prevents webhook timeout)

`@app.get("/health")`

- Health check endpoint
- Returns `{"status": "ok"}`
- Use for monitoring/load balancer checks

#### Session Management

Uses `InMemorySessionService` from Google ADK:

- Each PR gets a unique session ID: `{repo_name}_{pr_number}_{uuid}`
- Session is created before running agents
- Isolates context per PR (prevents cross-contamination)

### github_service.py

GitHub API wrapper built on PyGithub.

#### Key Functions

`__init__()`

- Authenticates with `GITHUB_TOKEN` from environment
- Creates `Github` client via `Auth.Token`
- Verifies connection by fetching authenticated user's login
- Logs connection status

`get_pr_metadata(repo_name, pr_number) → dict`

- Fetches comprehensive PR metadata:
- Title, description, state, author, created/updated timestamps
- Base and head branch refs + commit SHAs
- Statistics: commits, files changed, additions, deletions
- Labels, requested reviewers
- Per-file change details: filename, status (added/modified/removed/renamed), additions, deletions, patch size
- Logs a detailed ASCII-formatted report to console
- Returns dict with metadata for further processing

`get_pr_diff(repo_name, pr_number) → str`

- Fetches raw unified diff via GitHub API
- Uses `Accept: application/vnd.github.v3.diff` header to get plain diff text
- Calls `_parse_and_log_diff()` to log structure
- Returns diff as string (consumed by agents)

`_parse_and_log_diff(diff_text)`

- Parses unified diff using regex
- Splits by `diff --git` headers to separate files
- For each file:
- Extracts old/new filenames
- Counts additions (+) and deletions (-)
- Detects status (added/deleted/renamed/modified)
- Shows preview of first 3 changed lines
- Logs structured output to console for debugging

`post_comment(repo_name, pr_number, body)`

- Posts a comment on the PR via `pr.create_issue_comment()`
- Used to publish the AI review summary

`set_status_check(repo_name, sha, state, description, context)`

- Creates a commit status check on the commit SHA
- Parameters:
- `state`: `"pending"`, `"success"`, `"failure"`, `"error"`
- `description`: Human-readable message (max 140 chars)
- `context`: Status check name (e.g., `"AI-Review/security"`)
- GitHub displays these as status indicators on the PR page
- Required for blocking merges when `state == "failure"`
- **Permission note**: GitHub Token needs `repo:status` (Classic) or `Commit statuses: Read/Write` (Fine-grained)

### [agent.py](http://agent.py/)

The Google ADK agent hierarchy.

#### Agents Defined

`security_auditor` (LlmAgent)

- **Model**: `gemini-2.0-flash`
- **Output Key**: `"security_report"`
- **Focus**: Injection risks, hardcoded secrets, unsafe APIs, auth flaws, insecure dependencies
- **Output Format**: Markdown with `**File:** ... **Line:** ... **Issue:** ... **Fix:** ` blocks
- **Instruction**: Act as a Security Auditor; analyze diff for vulnerabilities; output specific locations and code fixes

`style_checker` (LlmAgent)

- **Model**: `gemini-2.0-flash`
- **Output Key**: `"style_report"`
- **Focus**: PEP8/ESLint violations, naming conventions, dead code, readability
- **Output Format**: Markdown with File/Line/Issue/Fix structure
- **Instruction**: Review for style consistency and best practices

`performance_analyzer` (LlmAgent)

- **Model**: `gemini-2.0-flash`
- **Output Key**: `"performance_report"`
- **Focus**: Algorithmic bottlenecks, O(n^2) loops, memory leaks, inefficient queries
- **Output Format**: Markdown with File/Line/Issue/Fix structure
- **Instruction**: Identify performance issues and suggest optimizations

`logic_verifier` (LlmAgent)

- **Model**: `gemini-2.0-flash`
- **Output Key**: `"logic_report"`
- **Focus**: Correctness, edge cases, off-by-one errors, null pointer issues, logic bugs
- **Output Format**: Markdown with File/Line/Issue/Fix structure
- **Instruction**: Verify logic correctness and identify potential bugs

`docs_reviewer` (LlmAgent)

- **Model**: `gemini-2.0-flash`
- **Output Key**: `"docs_report"`
- **Focus**: Missing docstrings, unclear comments, outdated README, API documentation
- **Output Format**: Markdown with File/Line/Issue/Fix structure
- **Instruction**: Ensure code is well-documented and maintainable

`parallel_review_swarm` (ParallelAgent)

- **Sub-agents**: All 5 review agents listed above
- **Behavior**: Executes all sub-agents concurrently
- **Output**: Session context populated with 5 reports (`security_report`, `style_report`, etc.)

`review_synthesizer` (LlmAgent - Decision Engine)

- **Model**: `gemini-2.0-flash`
- **Output Key**: `"final_review_decision"`
- **Input**: All 5 reports from session context (via templating: `{security_report}`, `{style_report}`, etc.)
- **Decision Logic**:
- High-severity security issue → `REQUEST_CHANGES` (blocks merge)
- Logic failure → `REQUEST_CHANGES`
- Only style/docs issues → `COMMENT` (doesn't block)
- No issues → `APPROVE`
- **Critical Instruction**: Preserve exact File/Line/Fix blocks from sub-agent reports (no generic summarization)
- **Output Format**: JSON only
``` 
{
  "decision": "APPROVE" | "REQUEST_CHANGES" | "COMMENT",
  "summary_markdown": "### PR Review Summary\n...",
  "checks": {
    "security": "success" | "failure",
    "style": "success" | "failure",
    "performance": "success" | "failure",
    "logic": "success" | "failure"
  }
}
```

`root_agent` (SequentialAgent)

- **Sub-agents**: `[parallel_review_swarm, review_synthesizer]`
- **Behavior**: Runs swarm first, then synthesizer with accumulated context
- **Entry Point**: This is the agent passed to `Runner()` in `server.py`

### sub_agents/ Directory

Contains individual agent definitions (`security_auditor.py`, `style_checker.py`, etc.)

Each file exports an `LlmAgent` instance with:

- Specialized instruction prompt
- Input parsing from JSON (`language`, `diff`, `files_changed`)
- Structured markdown output requirements
- Clear File/Line/Issue/Fix format enforcement


---

## Agent Specifications

### Sub-Agent Common Properties

| Property  | Value                                                                                |
| --------- | ------------------------------------------------------------------------------------ |
| ADK Class | `LlmAgent`                                                                           |
| Model     | `gemini-2.0-flash`                                                                   |
| Tools     | None (pure LLM reasoning)                                                            |
| Input     | JSON string: `{"repo": "...", "pr_number": 42, "language": "python", "diff": "..."}` |
| Output    | Markdown text with structured File/Line/Issue/Fix blocks                             |

### Security Auditor

| Attribute       | Value                                                                                                             |
| --------------- | ----------------------------------------------------------------------------------------------------------------- |
| Name            | `security_auditor`                                                                                                |
| Output Key      | `security_report`                                                                                                 |
| Analyzes        | Injection risks (SQL, XSS, Command), hardcoded secrets, unsafe API usage, auth/authz flaws, insecure dependencies |
| Severity Levels | HIGH (blocks merge), MEDIUM, LOW                                                                                  |
| Example Issue   | `Hardcoded API key found in config.py line 23`                                                                    |

### Style Checker

| Attribute     | Value                                                                           |
| ------------- | ------------------------------------------------------------------------------- |
| Name          | `style_checker`                                                                 |
| Output Key    | `style_report`                                                                  |
| Analyzes      | Formatting (PEP8, ESLint), naming conventions, dead/commented code, readability |
| Severity      | Does NOT block merge (feeds into COMMENT decision)                              |
| Example Issue | `Variable name 'x' violates naming convention (use 'user_count')`               |

### Performance Analyzer

| Attribute     | Value                                                                                         |
| ------------- | --------------------------------------------------------------------------------------------- |
| Name          | `performance_analyzer`                                                                        |
| Output Key    | `performance_report`                                                                          |
| Analyzes      | Algorithmic complexity (O(n^2)), inefficient queries (N+1), memory leaks, resource exhaustion |
| Severity      | Medium (can block if critical)                                                                |
| Example Issue | `Nested loop causes O(n^2) - use set lookup instead`                                          |

### Logic Verifier

| Attribute     | Value                                                                              |
| ------------- | ---------------------------------------------------------------------------------- |
| Name          | `logic_verifier`                                                                   |
| Output Key    | `logic_report`                                                                     |
| Analyzes      | Correctness, edge cases, off-by-one errors, null/undefined checks, type mismatches |
| Severity      | HIGH (blocks merge if logic is wrong)                                              |
| Example Issue | `Missing null check - will throw exception if user is None`                        |

### Documentation Reviewer

| Attribute     | Value                                                                           |
| ------------- | ------------------------------------------------------------------------------- |
| Name          | `docs_reviewer`                                                                 |
| Output Key    | `docs_report`                                                                   |
| Analyzes      | Missing docstrings, unclear comments, outdated README, public API documentation |
| Severity      | LOW (doesn't block, but surfaces in summary)                                    |
| Example Issue | `Public function missing docstring (add Args, Returns, Raises)`                 |

### Review Synthesizer (Decision Engine)

| Attribute         | Value                                                                                               |
| ----------------- | --------------------------------------------------------------------------------------------------- |
| Name              | `review_synthesizer`                                                                                |
| Output Key        | `final_review_decision`                                                                             |
| Input             | 5 reports from session context                                                                      |
| Output            | JSON: `{decision, summary_markdown, checks}`                                                        |
| Decision Rules    | Security HIGH → REQUEST_CHANGES; Logic fail → REQUEST_CHANGES; Only style → COMMENT; None → APPROVE |
| Critical Behavior | Preserves exact File/Line/Fix blocks from sub-agents (no summarization)                             |


---

## Implementation Details

### Async Bridge for ADK

Google ADK's `Runner.run_async()` is an async coroutine, but we need to call it from the FastAPI background task context which may have a running event loop.

``` 
async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=message):
    if event.is_final_response() and event.content:
        final_json_str = event.content.parts[0].text
```

FastAPI handles async natively, so no special bridge code is needed (unlike Streamlit which required a ThreadPoolExecutor).

### Code Fence Stripping

Gemini occasionally wraps JSON in markdown fences:

``` 
{
  "decision": "APPROVE"
}
```

The parsing logic handles this:

``` 
cleaned = final_json_str.strip()
if cleaned.startswith("```json"):
    cleaned = cleaned[7:]
if cleaned.endswith("```"):
    cleaned = cleaned[:-3]
result = json.loads(cleaned.strip())
```

### Diff Truncation

GitHub diffs for large PRs can exceed LLM context limits. The diff is truncated to 50KB before sending to agents:

``` 
agent_input = {
    "repo": repo_name,
    "pr_number": pr_number,
    "language": language,
    "diff": diff_text[:50000]  # Truncate if huge
}
```

A warning is logged if truncation occurs.

### Session Isolation

Each PR gets a unique session ID to prevent context contamination:

``` 
session_id = f"{repo_name.replace('/', '_')}_{pr_number}_{uuid.uuid4().hex[:6]}"
```

The `InMemorySessionService` stores context per session.

### Status Check Logic

GitHub status checks appear as visual indicators on the PR page:

``` 
🟡 AI-Review/security — pending
🟢 AI-Review/style — success
🔴 AI-Review/logic — failure
```

The merge button is blocked if ANY required check is in `failure` or `pending` state (configurable in GitHub branch protection rules).

### Background Task Pattern

The webhook handler immediately returns 202 Accepted:

``` 
background_tasks.add_task(process_pr_review, repo_name, pr_number, commit_sha)
return {"message": "Review queued"}
```

This prevents GitHub from timing out the webhook (10-second limit). The actual review runs asynchronously.


---

## API & Class Reference

### [server.py](http://server.py/)

#### `validate_environment_variables() → None`

Validates required env vars or exits with error message.

#### `async process_pr_review(repo_name: str, pr_number: int, commit_sha: str, language: str = "python") → None`

Main review pipeline. Runs as a background task.

#### `@app.post("/webhook")`

Webhook endpoint. Receives GitHub PR events.

**Request Headers:**

- `X-GitHub-Event`: Event type (e.g., `"pull_request"`)

**Request Body:** GitHub webhook payload (JSON)

**Response:** `{"message": "Review queued"}` (202 Accepted)

#### `@app.get("/health")`

Health check endpoint.

**Response:** `{"status": "ok"}` (200 OK)

### github_service.py

#### `GitHubService()`

Constructor. Authenticates with `GITHUB_TOKEN` and creates PyGithub client.

#### `get_pr_metadata(repo_name: str, pr_number: int) → dict`

Fetches PR metadata.

**Returns:**

``` 
{
    "title": str,
    "author": str,
    "files_changed": int,
    "additions": int,
    "deletions": int,
    "files": [{"filename": str, "status": str, "additions": int, "deletions": int, "changes": int}]
}
```

#### `get_pr_diff(repo_name: str, pr_number: int) → str`

Fetches raw unified diff.

**Returns:** Diff text (string)

#### `post_comment(repo_name: str, pr_number: int, body: str) → None`

Posts a comment on the PR.

#### `set_status_check(repo_name: str, sha: str, state: str, description: str, context: str) → None`

Sets a commit status check.

**Parameters:**

- `state`: `"pending"` | `"success"` | `"failure"` | `"error"`
- `description`: Human-readable message (max 140 chars)
- `context`: Check name (e.g., `"security"`)

**GitHub Context Name:** `AI-Review/{context}`

### [agent.py](http://agent.py/)

#### `security_auditor: LlmAgent`

Security review agent.

#### `style_checker: LlmAgent`

Style review agent.

#### `performance_analyzer: LlmAgent`

Performance review agent.

#### `logic_verifier: LlmAgent`

Logic review agent.

#### `docs_reviewer: LlmAgent`

Documentation review agent.

#### `parallel_review_swarm: ParallelAgent`

Orchestrates 5 sub-agents in parallel.

#### `review_synthesizer: LlmAgent`

Decision engine. Aggregates reports and outputs JSON verdict.

#### `root_agent: SequentialAgent`

Top-level orchestrator. Entry point for runner.


---

## GitHub Integration

### Webhook Setup

1. **Navigate to your GitHub repository** → Settings → Webhooks → Add webhook
2. **Configure webhook:**
- **Payload URL**: `https://your-server.com/webhook`
- **Content type**: `application/json`
- **Secret**: (optional, for security)
- **SSL verification**: Enable (recommended)
- **Which events**: Select "Let me select individual events" → Check **Pull requests**
3. **Save webhook**

GitHub will now send POST requests to your server when PR events occur.

### Local Testing with ngrok

For local development:

1. **Run the server locally:**
``` 
uvicorn server:app --reload
```
2. **Expose via ngrok:**
``` 
ngrok http 8000
```
3. **Copy the ngrok HTTPS URL** (e.g., `https://abc123.ngrok.io`)
4. **Set as webhook URL in GitHub**: `https://abc123.ngrok.io/webhook`

### Required GitHub Token Permissions

The `GITHUB_TOKEN` must have:

**Classic Token:**

- ✅ `repo` (Full control of private repositories)
- ✅ `repo:status` (Access commit status)

**Fine-Grained Token:**

- ✅ Repository access: Select repositories
- ✅ Permissions:
- **Pull requests**: Read and write
- **Commit statuses**: Read and write
- **Contents**: Read-only

### Branch Protection Rules (Optional)

To physically block merges when AI review fails:

1. Repository → Settings → Branches → Add branch protection rule
2. Branch name pattern: `main` (or your default branch)
3. ✅ **Require status checks to pass before merging**
4. Select status checks:
- `AI-Review/security`
- `AI-Review/logic`
- (optionally) `AI-Review/performance`
5. Save changes

Now PRs cannot be merged until these checks pass.


---

## How to Run

### 1. Install Dependencies

``` 
pip install -r requirements.txt
```

**requirements.txt:**

``` 
fastapi
uvicorn
python-dotenv
pydantic
google-adk
google-genai
PyGithub
requests
```

### 2. Set Environment Variables

Create a `.env` file in the project root (use [.env.example](https://markdown-confluence.herokuapp.com/md-editor?action=edit&xdm_e=https%3A%2F%2Fprocaltech.atlassian.net&xdm_c=channel-Narva.Apps.Markdown__md-editor&cp=%2Fwiki&xdm_deprecated_addon_key_do_not_use=Narva.Apps.Markdown&lic=none&userAccess=true&cv=1000.0.0-228febe09c7d&jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI3MTIwMjA6YmViYTdjMWItYzBiMy00OTUyLWFkYjktNjUyNTlhODdkZTJlIiwicXNoIjoiZDcwYmMzNDAyOWUyNTM2ZDk2ZjRmODk3MWMzYzgyYmZmN2VkYjRiNWJmNjQ5ODYyNzM4ODNkNWIzMGUxZDQ3ZSIsImlzcyI6IjZmNDZlMmY3LTQ5MDctMzI3Zi05MzUxLWRhNjZiMTljMGE0NCIsImNvbnRleHQiOnt9LCJleHAiOjE3NzE4NDMxODEsImlhdCI6MTc3MTg0MzAwMX0.VHHfEtiuyJCsrMjFoHCbCxPQRyP2X08v-SlXTgcSK0I#) as template):

``` 
# Google AI Configuration
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# GitHub Configuration
GITHUB_TOKEN=your_github_personal_access_token
```

**Get API Keys:**

- **Gemini API Key**: [Google AI Studio](https://aistudio.google.com/app/apikey)
- **GitHub Token**: GitHub → Settings → Developer settings → Personal access tokens → Generate new token

### 3. Run the Server

**Option A: Local Development**

``` 
uvicorn server:app --reload --port 8000
```

Server will start on `http://localhost:8000`.

**Option B: Production (Docker)**

``` 
docker-compose up --build
```

Server will start on `http://localhost:8000` inside the container.

### 4. Expose Webhook Endpoint

**For Local Testing:**

``` 
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`) and use it as the webhook URL in GitHub.

**For Production:**

Deploy to a cloud provider (AWS, GCP, Azure, Heroku, Render, etc.) with a public HTTPS endpoint.

### 5. Configure GitHub Webhook

1. Go to your repository → Settings → Webhooks → Add webhook
2. Set Payload URL to your server's `/webhook` endpoint
3. Select "Pull requests" events
4. Save

### 6. Test

1. Create a new branch in your repository
2. Make code changes and push
3. Open a Pull Request
4. The AI agent will automatically:
- Set status checks to "pending"
- Analyze the diff
- Post a detailed review comment
- Update status checks (success/failure)


---

## Tech Stack

| Tool                 | Role                                                                   |
| -------------------- | ---------------------------------------------------------------------- |
| **Google ADK**       | Agent orchestration (LlmAgent, ParallelAgent, SequentialAgent, Runner) |
| **Gemini 2.0 Flash** | LLM for code understanding and review generation                       |
| **FastAPI**          | Async webhook server and REST API                                      |
| **PyGithub**         | GitHub API client (fetch PR data, post comments, set status checks)    |
| **Pydantic**         | Request/response validation                                            |
| **python-dotenv**    | Environment variable loading                                           |
| **Uvicorn**          | ASGI server for FastAPI                                                |
| **Docker**           | Containerization for deployment                                        |
| **Python 3.11+**     | Runtime                                                                |


---

## Project Structure

``` 
pr_code_reviewer/
├── server.py                      # FastAPI webhook server & orchestrator
├── agent.py                       # Google ADK agent hierarchy
├── github_service.py              # GitHub API wrapper (PyGithub)
├── sub_agents/
│   ├── __init__.py
│   ├── security_auditor.py        # Security vulnerability detection
│   ├── style_checker.py           # Code style & formatting
│   ├── performance_analyzer.py    # Performance bottleneck detection
│   ├── logic_verifier.py          # Correctness & logic bugs
│   └── docs_reviewer.py           # Documentation completeness
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container build instructions
├── docker-compose.yml             # Docker orchestration
├── .dockerignore                  # Files excluded from Docker build
├── .env                           # Environment variables (create manually)
├── .env.example                   # Environment variable template
├── README.md                      # Quick start guide
└── DOCUMENTATION.md               # This comprehensive guide
```


---

## Methodology

| Concern                      | Approach                                                                             |
| ---------------------------- | ------------------------------------------------------------------------------------ |
| **Parallel execution**       | Google ADK `ParallelAgent` — all 5 sub-agents run simultaneously                     |
| **Structured output**        | Strict instruction prompts enforce File/Line/Issue/Fix format                        |
| **Decision logic**           | Synthesizer agent applies hardcoded rules (security fail → block)                    |
| **Webhook reliability**      | FastAPI background tasks prevent GitHub timeout                                      |
| **Session isolation**        | Unique session ID per PR (prevents context leaks)                                    |
| **Status check integration** | PyGithub sets commit statuses to block/allow merge button                            |
| **Error handling**           | Try/catch in background task; "error" status on failure                              |
| **Diff truncation**          | 50KB limit to fit LLM context window                                                 |
| **Code fence handling**      | Strip markdown fences from JSON responses                                            |
| **Language detection**       | Currently manual via `language` parameter (future: auto-detect from file extensions) |
| **Logging**                  | Structured logging with emoji markers for readability                                |


---

## Parallel Swarm Pattern

The **Parallel Swarm** pattern enables **zero-latency multi-perspective analysis** by dispatching multiple specialized agents simultaneously. Unlike sequential pipelines where agents wait for each other, all 5 review agents begin analyzing the instant the diff is available.

### Key Benefits

1. **Speed**: 5 agents run in ~T seconds instead of 5×T seconds sequentially
2. **Specialization**: Each agent is a domain expert (security expert ≠ style expert)
3. **Comprehensive Coverage**: No single agent needs to master all 5 concerns
4. **Structured Aggregation**: Decision Engine synthesizes findings with strict logic rules

### Google ADK Implementation

``` 
parallel_review_swarm = ParallelAgent(
    name="parallel_review_swarm",
    sub_agents=[
        security_auditor,
        style_checker,
        performance_analyzer,
        logic_verifier,
        docs_reviewer
    ],
    description="Runs all code review specialists in parallel."
)
```

The `ParallelAgent` manages:

- Concurrent execution of all sub-agents
- Context passing (all agents receive the same input)
- Session variable accumulation (outputs stored by `output_key`)
- Failure handling (continues even if one agent fails)

### Decision Engine

The `review_synthesizer` agent acts as the final arbiter:

``` 
review_synthesizer = LlmAgent(
    name="review_synthesizer",
    model=GEMINI_MODEL,
    instruction="""Apply strict Decision Rules:
    - IF any High Severity Security Issue → REQUEST_CHANGES
    - IF Logic/Correctness fail → REQUEST_CHANGES
    - IF only Style/Docs issues → COMMENT
    - IF no issues → APPROVE
    CRITICAL: Preserve exact File/Line/Fix blocks from sub-agents.""",
    output_key="final_review_decision"
)
```

This pattern ensures:

- **Consistent enforcement** of team standards (security always blocks)
- **Actionable feedback** with specific file/line/fix suggestions
- **Human-readable summaries** for developers


---

## Future Enhancements

- **Auto-detect programming language** from file extensions in diff
- **Inline PR comments** at specific line numbers (GitHub Review API)
- **Custom rule configuration** via YAML/JSON files
- **AI-suggested auto-fixes** via GitHub Suggestions feature
- **Historical tracking** of review decisions in database
- **Webhook signature verification** for security
- **Support for GitHub Checks API** (richer UI than commit statuses)
- **Multi-repository support** with per-repo configuration
- **Slack/Discord notifications** on review completion
