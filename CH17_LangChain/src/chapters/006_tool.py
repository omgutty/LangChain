"""
Chapter 006 - Custom tools.

The first chapter where the agent can DO something. So far the agent could only
answer from the model's own knowledge. Here it is given a calculator tool and
decides for itself when to call it.

The interesting part is the tool itself: it evaluates arithmetic without using
eval(), so a reply from the model can never execute arbitrary code.

Run from the src folder:
    python chapters/006_tool.py

Needs in .env:
    GOOGLE_API_KEY=<your key>
"""

# ast = "abstract syntax tree". ast.parse() turns a string of Python code into a
# tree of node objects, and ast.walk below inspects those nodes. We use it to
# understand an expression WITHOUT running it.
import ast

# operator holds the arithmetic as ordinary functions: operator.add(a, b) is
# a + b. Having them as functions lets us look one up in a dictionary instead of
# writing an if/else chain, and it means no '+' character is ever evaluated.
import operator

# Loads .env into os.environ (for the Google API key).
from dotenv import load_dotenv

# Builds the agent.
from langchain.agents import create_agent

# @tool is the decorator that turns a plain function into something an agent can
# call. Without it, create_agent(tools=[...]) would reject the function.
from langchain.tools import tool  # create custom tools

load_dotenv()

# eval() on text a model produced is arbitrary code execution. This walks the
# parsed expression instead, so only arithmetic can ever run.
#
# The mapping is: AST node class -> the function that performs it.
#   ast.Add   is the node for      a + b
#   ast.Sub   is the node for      a - b
#   ast.Mult  is the node for      a * b
#   ast.Div   is the node for      a / b
#   ast.Pow   is the node for      a ** b
#   ast.USub  is UNARY minus, i.e. a leading '-' such as -5
#
# Anything NOT in this dict is refused - that is the whole safety argument.
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
}


# Leading underscore = "internal helper, not part of the public interface".
# It takes a parsed node and returns a number.
def _safe_eval(node):
    # Base case: a literal number such as 438 or 2.5.
    # The isinstance(value, (int, float)) check matters - it rejects a string
    # constant, so "hello" cannot sneak through as a value.
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    # A binary operation (a + b). Check that the operator type is one we allow,
    # then look up its function in _OPS and apply it to the two sides.
    # This recurses: each side may itself be a smaller expression, which is how
    # something like (438/500)*100 gets evaluated correctly. Python's own
    # precedence rules are already baked into the shape of the tree.
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))

    # A unary operation, i.e. a single leading minus: -5.
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))

    # Anything else - a function call, an attribute, a name - is refused.
    # Raising here is fine because the @tool function below catches it.
    raise ValueError("only arithmetic is allowed")


# @tool turns this function into an agent tool. Three things get read off it to
# build the schema the MODEL sees:
#   1. the function name  -> qa_metric_calculator
#   2. the type hints     -> expression: str, returns str
#   3. the DOCSTRING      -> the tool's description
#
# Point 3 is the important one: the docstring is not documentation for humans,
# it is the prompt that tells the model WHEN to use this tool. That is why it
# spells out 'use this for pass rate, defect density, ...' instead of only
# describing what the function does.
@tool
def qa_metric_calculator(expression: str) -> str:
    """Calculate a QA metric from an arithmetic expression.

    Use this for pass rate, defect density, automation coverage, defect leakage
    or execution time. Input must be plain arithmetic with no words, for example
    '(438/500)*100' for a pass rate or '18/12' for defects per KLOC.
    """
    try:
        # ast.parse(..., mode="eval") parses exactly ONE expression - the mode is
        # what stops it accepting statements like 'import os'.
        # .body gives the expression node itself; _safe_eval walks it.
        result = _safe_eval(ast.parse(expression, mode="eval").body)

        # Return a STRING, not a number. Tools hand text back to the model, and
        # round(..., 2) keeps the reply tidy.
        return f"{round(result, 2)}"
    except Exception:
        # Catch broadly and RETURN the error rather than raising.
        #
        # This is the key design rule for agent tools: a raised exception kills
        # the whole agent run, but a returned string is something the model can
        # read and recover from - it sees "give me a plain arithmetic
        # expression" and tries again with better input.
        return "Error: give me a plain arithmetic expression, e.g. '(438/500)*100'"


# tools=[...] is what makes the agent able to act. The agent loop is then:
#   send the question + the tool schema -> model replies with a tool call ->
#   LangChain runs the function -> the result goes back to the model ->
#   model writes the final answer.
agent = create_agent(
    model="google_genai:gemini-flash-lite-latest",
    tools=[qa_metric_calculator],          # list of available tools
    system_prompt=(
        # "Use the tool whenever a number must be computed" - this instruction
        # plus the tool's own docstring is what decides the behaviour below.
        "You are a QA metrics assistant for a test automation team. "
        "Use the qa_metric_calculator tool whenever a number must be computed. "
        "State the formula you used, then the result with its unit."
    ),
)

# Three questions that prove the agent CHOOSES when to use the tool.
queries = [
    # maths -> the agent must call the tool.
    # It has to work out that '(438/500)*100' is the expression to send.
    "We ran 500 regression tests and 438 passed. What is the pass rate?",

    # maths again -> the agent must work out that defect density is 18/12.
    "A module of 12 KLOC has 18 defects. What is the defect density per KLOC?",

    # NO maths -> the agent answers from its own knowledge, no tool call.
    # This is the contrast case: a tool is not a fixed script that always runs.
    "What is the difference between smoke testing and sanity testing?",
]

for q in queries:
    print(f"\nQuestion: {q}")

    # .invoke() on the agent, same shape as 003. When a tool is needed, the
    # extra tool-call/tool-result messages appear inside result["messages"] too.
    result = agent.invoke({"messages": [{"role": "user", "content": q}]})

    # [-1] is the final message = the answered question. .text is its text.
    # (This differs from 001, where a raw model returned .content instead.)
    print("Agent:", result["messages"][-1].text)
