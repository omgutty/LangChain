# LangChain QA Automation

Learning and practice repository for building **AI-driven QA/testing pipelines** with
[LangChain](https://python.langchain.com/). It walks from the smallest possible LLM call
up to a full end-to-end pipeline that reads a Jira ticket, retrieves similar test cases
from a local RAG, writes a test plan, drives a real browser with Playwright, and reports
the verdict to a (dummy) Slack channel.

## Repository layout

| Folder | Purpose |
| --- | --- |
| `CH17_LangChain/` | My own practice workspace. Notes, exercises and variations I write while following the chapter. |
| `chapter_17_LangChain/` | Reference material copied from the instructor's chapter - the canonical examples and the full pipeline. |

## What lives in `chapter_17_LangChain/`

```
chapter_17_LangChain/
├─ E2E_QA_Pipeline.md          # Written walkthrough of the 8-step pipeline design
├─ LangChain_Notes.html        # Chapter notes (HTML)
└─ src/chapters/
   ├─ 001..013_*.py            # The chapter exercises, in order
   ├─ playwright_tools.py      # 30+ LangChain tools that drive a real browser
   ├─ tta_rag.py               # Tiny local RAG over the test-case corpus
   ├─ slack_tools.py           # Dummy Slack MCP (prints, never sends)
   ├─ fixtures/                # Offline Jira tickets (VWO-49, VWO-114)
   └─ rag_corpus/              # 20 TTACart test cases used as RAG documents
```

### The exercises, in order

| File | What it demonstrates |
| --- | --- |
| `001_Hello_LC.py` | Smallest LangChain + Groq LLM call |
| `002_Hello_Gemini.py` | First agent with Google Gemini |
| `003_Hello_Gemini_Steam.py` | Streaming tokens as they arrive |
| `004_SP.py` | System prompts / agent persona |
| `005_Agent_Parallel_Vs_Sequential.py` | `asyncio.gather` vs. sequential invocation |
| `006_Tool.py` | Custom tool (`@tool`) - a safe QA metric calculator |
| `007_MultiTool.py` | An agent choosing between multiple tools |
| `008_Structure_output.py` | Typed output with Pydantic `response_format` |
| `009_Playwright_Agent_Orch.py` | Browser agent on Groq |
| `010_Playwright_Agent_Orch_Deepseek.py` | Same task on DeepSeek (better tool discipline) |
| `011_FULL_E2E_Playwright_Agent_Orch_Deepseek.py` | Full purchase flow with assertions |
| `012_Fetch_JIRA_QA_Orch.py` | Jira ticket &rarr; test plan &rarr; browser run, with human gates |
| `013_FULL_E2E_Fetch_JIRA_Local_RAG_QA_Orch.py` | Everything: Jira + RAG + plan + browser + Slack |

## The end-to-end pipeline (`E2E_QA_Pipeline.md`)

1. **Fetch** Jira stories via JQL (REST v3, offline fixture fallback)
2. **Process** each story one by one
3. **Plan** a test plan grounded in historical plans via RAG
4. **Generate** test cases using the RAG pipeline
5. **Convert** test cases into Playwright automation flow `.md` files
6. **Execute** those `.md` files with Browser Bash
7. **Produce** a `result.json` with pass/fail, logs and errors
8. **Analyze** results - flakiness, RCA, triage - and push to a dashboard

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install python-dotenv langchain langchain-groq langchain-google-genai \
            langchain-deepseek pydantic requests playwright
playwright install chromium

# Optional - enables embedding-based RAG instead of keyword fallback
pip install fastembed numpy
```

### Environment variables

Create a `.env` next to the chapter scripts (it is git-ignored - never commit keys):

```ini
# LLM providers
LLM_MODEL=openai/gpt-oss-120b          # Groq model (001, 009, 012, 013)
GEMINI_LLM_MODEL=google_genai:gemini-flash-lite-latest
DEEPSEEK_MODEL=deepseek-flash          # 012/013 need thinking disabled for structured output
DEEPSEEK_API=your_deepseek_key

# Jira (012/013 fall back to offline fixtures when these are missing/expired)
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=your_jira_token

# Target app under test + reporting
TARGET_APP_URL=https://app.thetestingacademy.com/playwright/ttacart/
TARGET_APP_USER=standard_user
TARGET_APP_PASS=tta_secret
SLACK_MCP_URL=stdio://npx -y @modelcontextprotocol/server-slack
SLACK_CHANNEL=#qa-automation
```

## Running the examples

```bash
cd chapter_17_LangChain/src/chapters

python 001_Hello_LC.py
python 008_Structure_output.py
python 013_FULL_E2E_Fetch_JIRA_Local_RAG_QA_Orch.py VWO-49

# 013 options
#   --yes       skip the two human confirmation gates (CI)
#   --dry-run   stop after the plan, no browser
#   --no-rag    skip retrieval, to see what grounding is worth
```

`012` and `013` pause for confirmation before spending money or touching a real browser.
The Slack stage uses a **dummy MCP connection** - it prints what it would post and sends
nothing.

## Notes

- `playwright_tools.py` returns error strings instead of raising, because an agent can
  read `Error: no element matches #login` and adapt, but it cannot catch an exception.
- `tta_rag.py` degrades to keyword-overlap scoring if `fastembed` is not installed, so a
  demo still works offline with no downloads.
- Jira credentials are commonly the first thing to expire; `012`/`013` fall back to
  `fixtures/VWO-49.json` and `fixtures/VWO-114.json` so the demo keeps working.
