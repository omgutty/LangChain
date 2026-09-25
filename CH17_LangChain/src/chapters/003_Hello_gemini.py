"""
Chapter 003 - Hello Gemini.

The agent version of chapter 001: build an agent, ask one question, print the
whole answer at once. Read this next to 002 - the only real difference is
.invoke() versus .stream().

Run from the src folder:
    python chapters/003_Hello_gemini.py

Needs in .env:
    GEMINI_LLM_MODEL=google_genai:gemini-flash-lite-latest
    GOOGLE_API_KEY=<your key>
"""

# os is only here to read the model name out of the environment.
import os

# Loads .env into os.environ.
from dotenv import load_dotenv

# Builds the agent. No tools are passed, so it answers from the model's own
# knowledge only - it cannot look anything up or run anything.
from langchain.agents import create_agent

load_dotenv()


def main():
    # "google_genai:<model>" selects the provider and model in one string.
    # os.environ[...] raises KeyError if the variable is unset.
    agent = create_agent(model=os.environ["GEMINI_LLM_MODEL"])

    # Reads one line from the terminal.
    query = input("Ask your question: ")

    # .invoke() runs the agent once and waits for it to finish.
    #
    # The argument is a state dict, not a bare string - that is the main
    # difference from 001, where llm.invoke(query) took the string directly.
    # "messages" is the conversation history, and ("user", query) is shorthand
    # for {"role": "user", "content": query}.
    result = agent.invoke({"messages": [("user", query)]})

    # The agent returns the FULL conversation, not just the last reply.
    #   result["messages"]     -> the list (your question, then its answer)
    #   result["messages"][-1] -> the newest message = the agent's answer
    #   .text                  -> the text of that message
    #
    # Note: .text is used on a message object, which is why this differs from
    # 001's response.content - both return the text, from different object types.
    print(result["messages"][-1].text)


if __name__ == "__main__":
    main()
