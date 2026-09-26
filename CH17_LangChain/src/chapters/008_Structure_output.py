# ============================================================
# LangChain Agent - Structured Test Case Generation
# ============================================================
#
# This program:
# 1. Takes a user story as input
# 2. Sends it to an LLM through LangChain
# 3. Asks the LLM to generate test cases
# 4. Uses Pydantic to enforce the expected response structure
# 5. Reads the response as Python objects
#
# No manual JSON parsing is required.
# ============================================================


# ------------------------------------------------------------
# 1. IMPORT REQUIRED LIBRARIES
# ------------------------------------------------------------

# Literal is used to restrict a value to specific strings.
#
# Example:
# priority can ONLY be:
# "High", "Medium", or "Low"
#
# It cannot be something like "Critical" unless we add
# "Critical" to the Literal definition
from typing import Literal
# load_dotenv() reads variables from the .env file and
# loads them into the application's environment.
#
# Example .env:
#
# GOOGLE_API_KEY=your_api_key
#
# Then Python can access this environment variable.
from dotenv import load_dotenv
# BaseModel is the main Pydantic class.
#
# We use Pydantic to define the exact structure that
# we expect from the LLM response.
from pydantic import BaseModel

# create_agent() creates a LangChain agent.
#
# The agent can receive messages, call the configured LLM,
# and return the response in the requested format.
from langchain.agents import create_agent



# ------------------------------------------------------------
# 2. LOAD ENVIRONMENT VARIABLES
# ------------------------------------------------------------

# Read the .env file.
#
# This is normally used for API keys and other configuration.
load_dotenv()


# ------------------------------------------------------------
# 3. DEFINE THE STRUCTURE OF ONE TEST CASE
# ------------------------------------------------------------
    # 1) Define the response schema with Pydantic
class TestCase(BaseModel):
    
    """
    Represents ONE test case.

    Pydantic will validate the LLM response against this
    structure.
    """

    # Short name of the test case.
    #
    # Example:
    # "Verify user can add a product to the cart"
    title:str


    # Detailed explanation of what this test validates.
    description: str

       # Test execution steps.
    #
    # Example:
    # [
    #     "Login to the application",
    #     "Open the product page",
    #     "Click Add to Cart"
    # ]
    steps: list[str]

    # Expected result after performing the steps.
    expected_result: str
    
    # Priority is restricted to only three allowed values.
    #
    # Valid:
    #   High
    #   Medium
    #   Low
    #
    # Invalid:
    #   Critical
    #   P1
    #   Normal
    priority: Literal["High", "Medium", "Low"]

    # List of tags associated with the test case.
    #
    # Example:
    # [
    #     "Shopping Cart",
    #     "Functional",
    #     "Positive"
    # ]
    tags: list[str]

# ------------------------------------------------------------
# 4. DEFINE THE STRUCTURE OF THE COMPLETE RESPONSE
# ------------------------------------------------------------

class TestCaseList(BaseModel):
    """
    Represents the complete response from the LLM.

    Instead of returning a raw array like:

        [
            {...},
            {...}
        ]

    we wrap the array inside an object:

        {
            "test_cases": [
                {...},
                {...}
            ]
        }

    This provides a more predictable structured response.
    """
    # Tip: always wrap arrays inside an object (better compatibility, especially with Anthropic)
    test_cases: list[TestCase]

# ------------------------------------------------------------
# 5. CREATE THE LANGCHAIN AGENT
# ------------------------------------------------------------

agent= create_agent(
    # --------------------------------------------------------
    # LLM MODEL
    # --------------------------------------------------------
    #
    # LangChain uses this model to generate the response.
    #
    # "google_genai:" tells LangChain which model provider
    # integration to use.
    #
    # "gemini-flash-lite-latest" is the model name.
    #
    # You could also use another supported model provider.
    model="google_genai:gemini-flash-lite-latest",

     # --------------------------------------------------------
    # SYSTEM PROMPT
    # --------------------------------------------------------
    #
    # This defines the role and behavior of the agent.
    #
    # It tells the LLM:
    # - Act as a senior automation testing engineer
    # - Generate structured test cases
    # - Be detailed and professional
    #
    system_prompt=(
        "You are a senior automation testing engineer. "
        "Always return test cases in the exact structured "
        "JSON format requested. "
        "Be detailed and professional."
    ),

     # --------------------------------------------------------
    # RESPONSE FORMAT
    # --------------------------------------------------------
    #
    # This is the most important part of this example.
    #
    # We tell LangChain:
    #
    # "The final response must follow the TestCaseList
    #  Pydantic schema."
    #
    # LangChain + the model integration handles the
    # structured response instead of us manually parsing JSON.
    #
    response_format=TestCaseList,
)

# ------------------------------------------------------------
# 6. DEFINE THE USER STORY
# ------------------------------------------------------------

user_story = (
    "As a logged-in user, I want to add items to my "
    "shopping cart so that I can purchase them later."
)

# ------------------------------------------------------------
# 7. INVOKE THE AGENT
# ------------------------------------------------------------

result=agent.invoke(
    {
        # LangChain agents work with a list of messages.
         "messages": [

            {
                # This message is coming from the user.
                "role": "user",

            # The actual request sent to the agent.
            #
            # We insert the user story into the prompt using
            # an f-string.
                "content": (
                    f"Generate 2 detailed test cases for this "
                    f"user story: {user_story}"
                ),
            }
        ]    
    }
)

# ------------------------------------------------------------
# 8. ACCESS THE STRUCTURED RESPONSE
# ------------------------------------------------------------

print("=== Structured Output ===")


# Because we specified:
#
#     response_format=TestCaseList
#
# LangChain provides the structured response here.
#
# The result is NOT just a normal string.
#
# It is a Pydantic TestCaseList object.
#
# .test_cases gives us the list of TestCase objects.
test_cases = result["structured_response"].test_cases

# ------------------------------------------------------------
# 9. LOOP THROUGH THE TEST CASES
# ------------------------------------------------------------
for tc in test_cases:

    # tc is a TestCase Pydantic object.
    #
    # model_dump_json() converts the Pydantic object into
    # JSON formatted text.
    #
    # indent=2 makes the output easier to read.
    print(tc.model_dump_json(indent=2))

    # ------------------------------------------------------------
# 10. PRINT THE TOTAL NUMBER OF TEST CASES
# ------------------------------------------------------------

print(
    f"\nSuccessfully generated {len(test_cases)} test cases!"
)