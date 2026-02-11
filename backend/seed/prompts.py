from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client

from config import PROMPT_NAME

SYSTEM_TEMPLATE = """\
You are NovaPay's internal documentation assistant. Answer questions using ONLY the provided context.

Rules:
- Always cite which document(s) your answer comes from by referencing the source filename
- If the context doesn't contain enough information, say "I don't have documentation on that topic" — do NOT make up information
- if there is conflicting information on some of the numbers, give both of the numbers and let the user decide for themselves and flag it.


Context: {context}

Question: {question}"""

prompt = ChatPromptTemplate.from_messages([("system", SYSTEM_TEMPLATE)])


def seed_prompts() -> None:
    client = Client()
    url = client.push_prompt(
        prompt_identifier=PROMPT_NAME,
        object=prompt,
        description="NovaPay internal docs QA prompt — answers strictly from provided context with source citations.",
        is_public=False,
    )
    print(f"  Pushed '{PROMPT_NAME}' → {url}")
    print(f"  ⚠ Remember to manually add the ':prod' tag in the LangSmith UI")
