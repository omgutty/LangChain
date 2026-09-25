"""
Chapter 005 - Parallel vs Sequential agent calls.

The point of this file is SPEED. It sends the same agent four different
questions and runs all four at the same time instead of one after another.

Run from the src folder:
    python chapters/005_Agent_Parallel_Vs_Sequential.py

Needs in .env:
    GOOGLE_API_KEY=<your key>
    (the model is hard-coded below, so GEMINI_LLM_MODEL is not read here)
"""

# asyncio is what lets several calls be "in flight" at once. It provides
# asyncio.gather() and asyncio.run() below.
import asyncio

# time is used ONLY for timing - perf_counter() is a high-resolution stopwatch.
# perf_counter() is preferred over time.time() for measuring durations because it
# cannot jump if the system clock is adjusted, and it is far more precise.
import time

# Loads .env into os.environ. Needed so the Google API key is visible.
from dotenv import load_dotenv

# Builds the agent. As in 003, no tools are passed.
from langchain.agents import create_agent

load_dotenv()

# The agent is built here at MODULE level, not inside main() as in 001-003.
# That is deliberate: one agent is shared by all four calls below. Building it
# once and reusing it is cheaper than rebuilding it per question.
agent = create_agent(
    model="google_genai:gemini-flash-lite-latest",   # hard-coded this time
    system_prompt=(
        # system_prompt is the standing instruction sent with every request.
        # Because it says "in 10 bullet points", every answer comes back as
        # 10 bullets - useful when comparing four answers side by side.
        "You are an experienced software testing instructor. "
        "Explain each concept in 10 bullet points"
    ),
)

# Each entry is a dict: an id, a human label, and the actual prompt to send.
# Keeping them in a list is what makes the "loop over them" below possible.
questions = [
    {"id": 0, "topic": "LLM Eval", "prompt": "What is llm Eval?"},
    {"id": 1, "topic": "Smoke Testing", "prompt": "What is smoke testing?"},
    {"id": 2, "topic": "Sanity Testing", "prompt": "What is sanity testing?"},
    {"id": 3, "topic": "Regression Testing", "prompt": "What is regression testing?"},
]


# 'async def' marks this as a coroutine: a function that can pause at each
# 'await' and let other work run while it waits.
async def main():
    print("Creating langchain agent...\n")

    # Start the stopwatch. Store the reading now, subtract it at the end.
    start = time.perf_counter()

    # asyncio.gather() takes several awaitables and runs them CONCURRENTLY,
    # returning one list of results.
    #
    # The '*' unpacks the list so gather() receives four separate arguments
    # instead of one list object.
    #
    # The list comprehension builds four coroutines - note that nothing has
    # actually run yet at this point, because no 'await' has happened. They only
    # start when gather() is awaited.
    #
    # ainvoke() is the ASYNC version of the invoke() used in 003. It must be
    # awaited. This matters because the network wait is where all the time goes -
    # four waits happening at once take about as long as the slowest single one,
    # instead of the sum of all four.
    results = await asyncio.gather(*[
        agent.ainvoke({"messages": [{"role": "user", "content": q["prompt"]}]})
        for q in questions
    ])

    # gather() preserves INPUT ORDER, not completion order. results[0] is always
    # the answer to questions[0], even if question 2 finished first. That is what
    # makes zip() safe here.
    for q, result in zip(questions, results):
        print(f"{q['id']}. {q['topic']}")
        # Same shape as 003: the whole conversation comes back, [-1] is the
        # final reply, .content is its text.
        print(result["messages"][-1].content)
        print("-" * 70)

    # Elapsed seconds, rounded to 1 decimal place by the :.1f format.
    print(f"Finished {len(questions)} calls in {time.perf_counter() - start:.1f}s")


# asyncio.run() starts the event loop that makes the awaits work.
#
# NOTE: here it sits at module level, NOT inside an 'if __name__ == "__main__"'
# guard like 001-003. It still works when run directly, but it would also fire
# if this file were ever imported. The guard version is the safer habit.
asyncio.run(main())

# ---------------------------------------------------------------------------
# To see the SEQUENTIAL version for comparison (this is the "vs" in the name),
# replace the gather block above with:

#     results = []
#     for q in questions:
#         results.append(await agent.ainvoke(
#             {"messages": [{"role": "user", "content": q["prompt"]}]}))

# Each await now blocks until that one call finishes before the next starts.
# The answers are identical; only the total time changes - roughly 4x the
# elapsed time, because four network waits happen one after another instead of
# at the same time.
# ---------------------------------------------------------------------------
