# ============================================================
# LangChain + Groq + Playwright Agent
# ============================================================
#
# This program creates an AI agent that can control a browser
# using Playwright tools.
#
# The LLM decides:
#   - which browser action to perform
#   - what order to perform the actions
#   - what information to use from the browser
#   - when the test is complete
#
# Playwright actually performs the browser actions.
# ============================================================



import asyncio
from dotenv import load_dotenv
from langchain.agents import create_agent 
from langchain_groq import chatGroq

from playwright_tools import PLAYWRIGHT_TOOLS

import os

