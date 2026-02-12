"""LLM-as-judge correctness evaluator for LangSmith experiments."""

from langchain_openai import ChatOpenAI
from langsmith.schemas import Example, Run

JUDGE_PROMPT = """\
You are an expert evaluator. Given a question, a reference answer, and a predicted \
answer, judge the predicted answer's correctness.

First, identify the KEY CLAIMS in the reference answer. Then check whether the \
predicted answer covers each one. Do not penalize for different wording, extra \
detail, or formatting differences. Only penalize for factually incorrect statements \
or missing key claims.

Key claims include: specific numbers, named sources, causal explanations, caveats, \
and warnings that appear in the reference.

Scoring:
- 1.0 = all key claims are present and nothing is factually wrong
- 0.75 = one key claim is missing but nothing is wrong
- 0.5 = multiple key claims missing or a minor inaccuracy
- 0.25 = mostly wrong but contains a relevant fact
- 0.0 = completely wrong or irrelevant

Respond in this exact format (no other text):
Key claims: <numbered list of key claims from the reference>
Covered: <which key claims the predicted answer covers>
Missing: <which key claims are missing, or "none">
Wrong: <any factually incorrect statements, or "none">
Score: <float between 0.0 and 1.0>

Question: {question}

Reference answer: {reference}

Predicted answer: {predicted}"""


def correctness_evaluator(run: Run, example: Example) -> dict:
    """Compare predicted answer against reference and return a 0-1 score with reasoning."""
    predicted = run.outputs.get("answer", "")
    reference = example.outputs.get("answer", "")
    question = example.inputs.get("question", "")

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    formatted = JUDGE_PROMPT.format(
        question=question,
        reference=reference,
        predicted=predicted,
    )
    response = llm.invoke(formatted)

    text = response.content.strip()
    print(f"\n{'='*60}")
    print(f"Q: {question[:80]}")
    print(f"Reference: {reference[:120]}...")
    print(f"Predicted: {predicted[:120]}...")
    print(f"Judge response:\n{text}")
    print(f"{'='*60}\n")
    score = 0.0
    reasoning_parts = []

    for line in text.splitlines():
        if line.startswith("Score:"):
            try:
                score = float(line.split("Score:", 1)[1].strip())
                score = max(0.0, min(1.0, score))
            except ValueError:
                score = 0.0
        else:
            reasoning_parts.append(line)

    return {"key": "correctness", "score": score, "comment": "\n".join(reasoning_parts).strip()}
