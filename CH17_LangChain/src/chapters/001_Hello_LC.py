"""
Chapter 001 - Hello LangChain (Groq).

The smallest possible LangChain program: send one question to an LLM and print
the answer. No agent, no tools, no memory, no streaming - just the model.

Run from the src folder:
    python chapters/001_Hello_LC.py

Needs in .env:
    LLM_MODEL=<a Groq model id, e.g. openai/gpt-oss-120b>
    GROQ_API_KEY=<your key>          # read by the Groq SDK itself, not by this file
"""

# UNUSED IMPORT - leave it or delete it, it changes nothing here.
# pyexpat is the C module Python uses to parse XML. It has a 'model' attribute
# (a version string like "expat_2.x.x"), which is almost certainly not what was
# wanted. It looks like a stray auto-import left over from the reference file.
# If you delete this line the program still runs.
from pyexpat import model

# load_dotenv reads key=value pairs out of a .env file and puts them into
# os.environ, so secrets live in a file instead of in the source code.
from dotenv import load_dotenv

# ChatGroq is LangChain's wrapper around the Groq API. "Chat" means it talks in
# messages (system/user/assistant) rather than raw text completion.
from langchain_groq import ChatGroq

# os is the standard library module used here only to READ environment variables.
# os.getenv("LLM_MODEL") returns the value that load_dotenv() just loaded.
import os

# Must be called BEFORE ChatGroq is created below, otherwise LLM_MODEL and the
# API key are not in os.environ yet and the call fails.
load_dotenv()


def main():

    # ChatGroq(...) builds the client. This line does not call the API yet, it
    # only configures it.
    #   model=       which model to use, read from .env so it is not hard-coded
    #   temperature= how random the answer is. 1 = varied/creative, 0 = as
    #                repeatable as possible. For tests you want 0.
    llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=1)

    # input() blocks and waits for you to type one line in the terminal.
    # Whatever you type is stored in 'query' as a string.
    query = input("Enter the question: ")

    # .invoke() is the simplest call: send the prompt, wait for the WHOLE reply.
    # It returns an AIMessage object, not a plain string.
    response = llm.invoke(query)

    # .content is the actual text inside that AIMessage. Printing the object
    # itself would show extra metadata, so we print .content.
    print(response.content)


# This guard means: only run main() when the file is executed directly
# (python chapters/001_Hello_LC.py). If another file did "import 001_Hello_LC",
# this block is skipped and nothing runs on its own.
if __name__ == "__main__":
    main()
