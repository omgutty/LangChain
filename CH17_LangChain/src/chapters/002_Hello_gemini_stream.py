"""
Chapter 002 - Hello Gemini (streaming).

Same idea as chapter 001, but two differences:
  1. it uses create_agent() instead of a raw model, and
  2. it prints the answer token by token as the model writes it, instead of
     waiting for the whole reply before showing anything.

Run from the src folder:
    python chapters/002_Hello_gemini_stream.py

Needs in .env:
    GEMINI_LLM_MODEL=google_genai:gemini-flash-lite-latest
    GOOGLE_API_KEY=<your key>
"""

# os is used here to read an environment variable with os.environ["..."].
# That raises KeyError if the variable is missing - see the note below.
import os

# Puts the .env file's contents into os.environ.
from dotenv import load_dotenv

# create_agent() is LangChain 1.x's way of building an agent. An agent is a model
# plus a loop: it can call tools, see the results, and decide what to do next.
# Here we pass no tools, so it just answers directly.
from langchain.agents import create_agent

# Must run before os.environ[...] is read below.
load_dotenv()


def main():
    # "provider:model" syntax - the part before ':' tells LangChain which
    # integration to use (google_genai, installed as langchain-google-genai).
    # This is why there is no "from langchain_google_genai import ..." at the top.
    #
    # os.environ[...] (not os.getenv) will crash with KeyError if GEMINI_LLM_MODEL
    # is missing from .env. That is deliberate here: it fails loudly and early.
    agent = create_agent(model=os.environ["GEMINI_LLM_MODEL"])

    # NOTE: this line asks the user for a question, but the messages sent below
    # are hard-coded, so 'query' is never used. The reference file has the same
    # quirk. To actually use it, swap the user content for ('user', query).
    query = input("Ask your question: ")

    print("\nStreaming Response:")

    # .stream() instead of .invoke(): it yields results as they are produced
    # rather than returning one finished object.
    #
    # The input is a state dict with a "messages" key. Each message is a dict with:
    #   role    - "system" sets the persona/instructions, "user" is the question
    #   content - the text
    #
    # stream_mode="messages" says: emit one item per message chunk (i.e. per
    # token batch). Other modes exist for streaming whole steps instead.
    for token, metadata in agent.stream(
        {
            "messages": [
                {"role": "system", "content": "You are a software testing instructor."},
                {"role": "user", "content": "Explain LLM Eval in 3000 words blog"},
            ]
        },
        stream_mode="messages",
    ):
        # token is an AIMessageChunk (the piece just produced); metadata holds
        # extra info such as which node produced it. We only print the text.
        #
        # end=""      stops print() adding a newline after every chunk
        # flush=True  forces it to the screen immediately instead of being
        #             buffered - without this the "streaming" would appear all
        #             at once at the end.
        print(token.text, end="", flush=True)

    # One final newline so the shell prompt starts on its own line.
    print()


if __name__ == "__main__":
    main()
