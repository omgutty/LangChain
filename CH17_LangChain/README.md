# CH17_LangChain - My Practice Workspace

This folder is where I practice and experiment while working through Chapter 17.

The reference code lives in [`../chapter_17_LangChain`](../chapter_17_LangChain).
Here I rewrite the exercises myself, try variations, and keep notes as I go.

> This README is my own runbook. It records the exact steps I use to set the project
> up, so next time I can follow it top to bottom without re-deriving anything.

---

## Current state of this folder

```
CH17_LangChain/
├─ README.md          # this file
└─ src/
   └─ .venv/          # Python 3.13.14 virtual environment (git-ignored)
```

The venv currently sits inside `src\`. The recommended layout puts it at the project
root instead - see **Where the venv should live** below - so the steps that follow
assume `CH17_LangChain\.venv`.

Everything below is the procedure I run from a fresh clone.

---

## Toolchain

| Tool | Version I use | Why |
| --- | --- | --- |
| `uv` | latest | Creates the venv and installs packages - much faster than plain pip |
| Python | 3.13 (uv-managed) | LangChain 1.x needs >= 3.10; 3.13 is already downloaded by `uv` |
| PowerShell | Windows PowerShell 5.1 | Runs the activation script (Step 3 covers it if Windows blocks it) |

Check what is available before starting:

```powershell
uv --version
uv python list          # shows which Python versions are already installed
```

`uv python list` marks already-downloaded versions with a real path; the rest say
`<download available>`. On this machine `cpython-3.13` is already present, so no
download happens.

---

## Where the venv should live

I first created it from a `cd src` prompt, so it landed here:

```
CH17_LangChain\src\.venv
```

That works, but the venv belongs at the **project root** instead:

```
CH17_LangChain\.venv
```

Why it matters - `uv run` locates a venv by checking the current folder and then
walking **up** the tree. It never searches downwards:

| I run from | venv in `src\` | venv at root |
| --- | --- | --- |
| `CH17_LangChain\` | not found | found |
| `CH17_LangChain\src\` | found | found |
| `CH17_LangChain\src\chapters\` | found | found |

So a `src\.venv` only works while I always run from `src\` or deeper. At the root it
works from anywhere in the project, it is what VS Code auto-detects when choosing an
interpreter, and it leaves room for a `pyproject.toml` at the root later (which
expects `.venv` beside it).

To move it - nothing is installed yet, so nothing is lost:

```powershell
cd D:\Projects\LangChain\CH17_LangChain
Remove-Item -Recurse -Force src\.venv
uv venv
```

If I decide to keep it in `src\`, then every `uv` command below has to be run from
`src\`.

---

## Step 1 - Open the folder

```powershell
cd D:\Projects\LangChain\CH17_LangChain
```

I work in **this** folder, not the reference folder. The reference is read-only for me.

---

## Step 2 - Create the virtual environment

```powershell
uv venv
```

What this does: creates a `.venv` folder in the current directory. No `--python`
flag is needed - `uv` picks the newest interpreter it already has, 3.13.14 on this
machine. The `.venv` folder is already covered by the repo `.gitignore` (and by uv's
own `.venv\.gitignore`), so it is never committed.

This is the command that actually worked. I tried `python -m venv .venv` first and it
failed with *"Python was not found; run without arguments to install from the
Microsoft Store"*, because `python` on PATH is only a Store alias. `py` is not
installed either. `uv venv` needs neither - it uses its own interpreter.

Real output:

```
Using CPython 3.13.14
Creating virtual environment at: .venv
Activate with: .venv\Scripts\activate
```

> If `uv` has to download the interpreter the first time, that is normal and only
> happens once.

---

## Step 3 - Activate the environment

```powershell
.venv\Scripts\Activate.ps1
```

On this machine it activated straight away, no error. Windows *can* block it with
*"running scripts is disabled on this system"* - **only if that happens**, relax the
policy for **this terminal session only** and activate in the same command:

```powershell
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& .venv\Scripts\Activate.ps1)
```

- `-Scope Process` means the change dies when the terminal closes - it does not
  weaken the machine-wide setting.
- The prompt is then prefixed with the venv name, which is how I know it worked. It
  showed `(src)` because the venv lived in `src\`; from the project root it shows
  `(CH17_LangChain)`.

To confirm the interpreter is the venv one:

```powershell
python -c "import sys; print(sys.executable)"
```

The path must contain `CH17_LangChain\.venv`. If it does not, the venv is not active.

---

## Step 4 - Install LangChain and the model providers

With the venv active:

```powershell
uv pip install langchain langchain-groq langchain-google-genai langchain-deepseek python-dotenv requests
```

`uv pip` and not plain `pip` - a uv-created venv has no pip inside it, so
`pip install ...` fails with *"No module named pip"*.

What each one is for:

| Package | Used for |
| --- | --- |
| `langchain` | Core library - `create_agent`, `@tool`, structured output |
| `langchain-groq` | `ChatGroq` - fast models for planning calls |
| `langchain-google-genai` | Gemini, referenced as `google_genai:gemini-flash-lite-latest` |
| `langchain-deepseek` | `ChatDeepSeek` - drives the browser agent |
| `python-dotenv` | Loads my API keys from `.env` |
| `requests` | Plain HTTP calls inside custom tools |

`pydantic` comes in automatically as a LangChain dependency - I never install it by hand.

If I want the optional embedding-based RAG (instead of the keyword fallback):

```powershell
uv pip install fastembed numpy
```

---

## Step 5 - Install the Playwright browser

The Python package and the browser binary are two separate installs. Installing the
package alone is not enough - the browser has to be downloaded too:

```powershell
uv pip install playwright
uv run playwright install chromium
```

`playwright install chromium` fetches the Chromium build Playwright drives. It is a
few hundred MB and only needs doing once per machine.

---

## Step 6 - Create the `.env` file

Create a file called `.env` in **this** folder (`CH17_LangChain\.env`). It is
git-ignored - keys never leave my machine.

```ini
# LLM providers
LLM_MODEL=openai/gpt-oss-120b
GEMINI_LLM_MODEL=google_genai:gemini-flash-lite-latest
DEEPSEEK_MODEL=deepseek-flash
DEEPSEEK_API=your_deepseek_key

# Jira (optional - the chapter falls back to offline fixtures if unset)
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=your_jira_token

# App under test
TARGET_APP_URL=https://app.thetestingacademy.com/playwright/ttacart/
TARGET_APP_USER=standard_user
TARGET_APP_PASS=tta_secret

# Reporting
SLACK_MCP_URL=stdio://npx -y @modelcontextprotocol/server-slack
SLACK_CHANNEL=#qa-automation
```

Note: the DeepSeek SDK looks for `DEEPSEEK_API_KEY`, but the env var is
`DEEPSEEK_API`. The scripts pass it explicitly with `api_key=os.environ["DEEPSEEK_API"]`
for that reason.

---

## Step 7 - Verify the install before writing any code

This is the check I run every time, before blaming my own code:

```powershell
uv pip list
```

```powershell
uv run python -c "import langchain, langchain_groq, langchain_deepseek; print('langchain', langchain.__version__)"
```

```powershell
uv run python -c "from langchain.agents import create_agent; from langchain.tools import tool; print('API OK')"
```

If `create_agent` imports cleanly, the SDK versions match the chapter code. If it
fails, I installed a LangChain 0.x -

```powershell
uv pip install -U langchain
```

---

## Step 8 - Run an exercise

```powershell
uv run python src\chapters\001_Hello_LC.py
```

`uv run` executes the script inside `.venv` without needing activation to be
perfectly set up, so this is also my fallback when activation misbehaves.

Two useful flags for the bigger scripts (`012`, `013`):

| Flag | Effect |
| --- | --- |
| `--yes` | Skip the human confirmation gates (for unattended runs) |
| `--dry-run` | Stop after the plan - no browser is launched |
| `--no-rag` | Skip retrieval, to see what grounding is actually worth |

Example:

```powershell
uv run python src\chapters\013_FULL_E2E_Fetch_JIRA_Local_RAG_QA_Orch.py VWO-49 --dry-run
```

---

## Everyday cheat sheet

```powershell
# Activate, from the project root
.venv\Scripts\Activate.ps1

# ...or, only if Windows blocks it:
# (Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& .venv\Scripts\Activate.ps1)

# Add a new package later
uv pip install <package>

# See what is installed
uv pip list

# Run anything
uv run python src\chapters\<file>.py
```

---

## The loop I follow for each new exercise

1. Copy the reference file from `..\chapter_17_LangChain\src\chapters\` as a starting point.
2. Retype it myself instead of pasting - that is the whole point of this folder.
3. Run it: `uv run python src\chapters\<file>.py`.
4. When it breaks, read the traceback from the **bottom** up; the last line is the real error.
5. Note what was non-obvious in `notes/`.
6. Commit and push.

---

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `.venv\Scripts\Activate.ps1 cannot be loaded because running scripts is disabled` | PowerShell execution policy | Use the `Set-ExecutionPolicy -Scope Process` line from Step 3 |
| `Python was not found; run without arguments to install from the Microsoft Store` | `python` on PATH is only the Store alias | Use `uv venv` and `uv run` - do not use `python -m venv` |
| `uv` reports no virtual environment found | venv is in `src\` but I ran from the root | Run from `src\`, or move the venv to the root |
| `ModuleNotFoundError: No module named 'langchain'` | venv not active, or installed globally | Activate the venv, or run with `uv run python ...` |
| `No module named pip` inside the venv | uv-created venvs do not ship pip | Use `uv pip install ...`, never plain `pip install ...` |
| `ImportError: cannot import name 'create_agent'` | LangChain 0.x installed | `uv pip install -U langchain` |
| `Missing key inputs argument` / API key error | `.env` missing, or wrong var name | Confirm `.env` sits in this folder and the name matches the code |
| Playwright: `Executable doesn't exist` | Browser binary not installed | `uv run playwright install chromium` |
| Wrong Python picked up | venv not active | `python -c "import sys; print(sys.executable)"` must show `.venv` |

---

See the [root README](../README.md) for what the reference chapter contains and the
full 001-013 exercise index.
