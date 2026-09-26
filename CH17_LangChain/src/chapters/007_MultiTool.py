"""
Chapter 007 - Multiple tools (tool routing).

THE IDEA
    Chapter 006 gave the agent ONE tool. This chapter gives it TWO, and the agent
    decides WHICH to use - or whether to use either. That decision is called
    routing, and the model makes it by reading each tool's docstring.

PROGRAM STRUCTURE (top to bottom)

    1. SETUP ....... imports, load_dotenv(), the shared HEADERS constant
    2. TOOL 1 ...... search_tool       - "find something on the web"
    3. TOOL 2 ...... web_content_tool  - "fetch this exact URL"
    4. AGENT ....... create_agent() with BOTH tools registered
    5. TEST DATA ... the three queries
    6. RUN ......... loop over the queries and print each answer

RUNTIME FLOW - what happens for each question

        question
           |
           v
    the model reads: system_prompt + the docstring of every registered tool
           |
           +--> "I need to find something"   -> search_tool(query)
           +--> "I was handed a URL"         -> web_content_tool(url)
           +--> "I can answer this myself"   -> no tool call at all
           |
           v
    the tool's STRING result is fed back to the model
           |
           v
    the model writes the final answer -> printed by the loop

Run from the src folder:
    python chapters/007_MultiTool.py

Needs in .env:
    GOOGLE_API_KEY=<your key>
"""

# ---------- 1. SETUP ----------

# re is the regular-expression module. It is used twice below: once to PULL the
# <title> out of a page, once to STRIP all HTML tags out of a page.
import re

# requests makes the actual HTTP calls. This is the first chapter that talks to
# the outside world, which is why it is the first to import this.
import requests                            # call external APIs and pages

# Loads .env into os.environ.
from dotenv import load_dotenv

# Builds the agent.
from langchain.agents import create_agent

# The decorator that turns a function into a tool.
from langchain.tools import tool

load_dotenv()

# A module-level CONSTANT (upper case is the Python convention for that).
#
# Why it is needed: `requests` normally identifies itself as
# "python-requests/2.x", and many sites - DuckDuckGo included - return an empty
# or blocked page to that agent string. Pretending to be a normal browser avoids
# it. It is defined once here and reused by BOTH tools, rather than repeated.
#
# HONEST CAVEAT: this is a well-known, slightly sneaky trick. Some sites also
# serve an anti-bot / rate-limit response (DuckDuckGo answers 202 rather than
# 200), and the tools below do not check the status code, so a blocked page is
# indistinguishable from a successful one.
HEADERS = {"User-Agent": "Mozilla/5.0"}


# ---------- 2. TOOL 1: web search ----------

# Tool 1: search the web and return the title of the results page
#
# The docstring below is NOT documentation for you - it is the text the model
# reads to decide when to call this tool. It is the tool's "when to use me".
@tool
def search_tool(query: str) -> str:
    """Search the web for a query and return the title of the results page."""
    try:
        # requests.get() performs an HTTP GET.
        #   params={...}  is appended to the URL and encoded for you, so a query
        #                 with spaces or '?' becomes ?q=What+is+Playwright%3F
        #                 instead of producing a broken URL.
        #   headers=...   sends the browser-like User-Agent from above.
        #   timeout=10    gives up after 10s. Without it a hung request would
        #                 block the agent forever - always set a timeout on a
        #                 network call inside a tool.
        res = requests.get("https://html.duckduckgo.com/html/",
                           params={"q": query}, headers=HEADERS, timeout=10)

        # Pull the first <title>...</title> out of the HTML.
        #   (.*?)  non-greedy, so it stops at the FIRST </title> rather than
        #          swallowing the rest of the document.
        #   re.S   makes '.' match newlines too, because titles can span lines.
        match = re.search(r"<title>(.*?)</title>", res.text, re.S)

        # group(1) is the first capture group, i.e. the text inside the tags.
        # strip() removes the surrounding whitespace. If nothing matched, return
        # a readable sentence instead of None.
        #
        # VERIFIED BEHAVIOUR: whatever the query, this returns 'DuckDuckGo' -
        # the title of the results PAGE, not the search results themselves. So
        # the tool proves the ROUTING works, but it is not a usable search. To
        # return real results you would parse the result blocks out of the HTML.
        return match.group(1).strip() if match else "No title found"
    except Exception:
        # Same rule as chapter 006: return an error string, never raise.
        # A raised exception ends the agent run; a returned string lets the
        # model see the failure and decide what to do next.
        return "Error performing search"


# ---------- 3. TOOL 2: fetch a page ----------

# Tool 2: fetch a URL and return its plain text (first 1000 characters)
#
# Read the two docstrings side by side - this is the whole routing lesson:
#   tool 1 says "SEARCH THE WEB for a query"  -> give me words to look up
#   tool 2 says "FETCH THE CONTENT OF A URL"  -> give me a link
# The model picks between them using nothing but that wording.
@tool
def web_content_tool(url: str) -> str:
    """Fetch the content of a web page from a URL and return its plain text."""
    try:
        # No params= here, because this tool is handed a complete URL.
        res = requests.get(url, headers=HEADERS, timeout=10)

        # Strip every HTML tag: '<[^>]*>' means "a < followed by any characters
        # that are not >, followed by >". Removing them leaves the raw text.
        #
        # HONEST CAVEAT: this is a crude strip, not a page-to-text converter. It
        # leaves behind <script> and <style> CONTENT (only the tags are removed),
        # plus embedded JSON-LD. VERIFIED: the first 1000 characters of a real
        # Playwright doc page are mostly '"@context":"https://schema.org"...'
        # and JavaScript - barely readable. A proper extractor (trafilatura,
        # BeautifulSoup with a parser) is what a production tool would use.
        text = re.sub(r"<[^>]*>", "", res.text)   # strip HTML tags

        # Return only the first 1000 characters. The point is to protect the
        # model's context window: a full page would burn thousands of tokens,
        # and this is a demo of tool routing, not of summarisation.
        return text[:1000]
    except Exception:
        return "Error fetching web content"


# ---------- 4. AGENT ----------

# The only line that differs from chapter 006 is the tools list - it now holds
# TWO functions instead of one. Everything else about the agent is unchanged.
#
# How routing actually happens: LangChain converts each function into a schema
# (name, parameters, docstring) and sends ALL of them to the model with every
# request. The model then answers with either normal text or a request to call
# one of the tools. Nothing in this file decides which tool runs.
agent = create_agent(
    model="google_genai:gemini-flash-lite-latest",
    tools=[search_tool, web_content_tool],  # pass both tools in the list
    system_prompt=(
        # The system prompt nudges the model to actually use its tools. Combined
        # with the docstrings, this is the entire routing policy. Notice it does
        # not name the tools - the model maps "search" and "fetch content" onto
        # the two docstrings itself.
        "You are a helpful automation testing assistant. "
        "Use the available tools to search the web and fetch content when needed."
    ),
)

# ---------- 5. TEST DATA ----------

# Three queries chosen to exercise three different outcomes. The comments are
# the author's intent - whether the model agrees is not guaranteed, which is
# exactly what makes tool routing interesting to observe.
queries = [
    "What is Playwright?",                                # general info (may use search)
    "Search for the Appium official website",             # needs search_tool
    "Get content from https://playwright.dev/docs/intro", # needs web_content_tool
]

# ---------- 6. RUN ----------

for q in queries:
    print(f"\nQ: {q}")

    # One agent call per question, same shape as chapters 003 and 006.
    result = agent.invoke({"messages": [{"role": "user", "content": q}]})

    # Two things worth noticing on this line:
    #   1. .content, not .text. Both give the message's text; .text is the newer
    #      alias. Chapters 005 and 006 use .text, this file uses .content. Pick
    #      one and stay consistent.
    #   2. There is no printing of tool calls here. To SEE the routing happen,
    #      walk result["messages"] and print any message that has .tool_calls -
    #      that is exactly what 009 does with the Playwright agent.
    print(f"Agent: {result['messages'][-1].content}")


# ---------------------------------------------------------------------------
# MACHINE NOTE - this bit is specific to this laptop, not to LangChain.
#
# Both tools failed here with:
#   SSLError: CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate
#
# Cause: something on the network path re-signs HTTPS traffic with a root CA
# that is present in the WINDOWS certificate store but NOT in certifi's bundle.
# Python's requests trusts only certifi, so it rejects the certificate. It is
# why `uv` and the Playwright browser work (they use the OS store) while these
# two tools do not.
#
# Fix, using truststore (already installed as a langchain dependency) - the two
# lines below must run BEFORE requests is used:
#
#     import truststore
#     truststore.inject_into_ssl()
#
# Also worth clearing a stale variable that points at another project's certs:
#
#     Remove-Item Env:\SSL_CERT_FILE
#
# With that in place both tools return real data. Without it they return their
# "Error ..." strings, and the agent still answers - just with no data.
# ---------------------------------------------------------------------------
