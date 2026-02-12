"""LLM-as-judge prompt for the LangSmith UI online evaluator.

To set up as an online evaluator in the LangSmith UI:
  1. Go to Datasets → novapay-qa-golden → click "+ Evaluator"
  2. Choose "LLM-as-judge", select model (GPT-4o)
  3. Paste the LANGSMITH_UI_JUDGE_PROMPT below
  4. Map variables via the dropdowns:
       {{input.question}}           → dataset input "question"
       {{referenceOutput.answer}}   → reference output "answer"
       {{output.output.content}}    → experiment run output (AIMessage content)
  5. Set feedback key to "correctness", type to Continuous (0.0–1.0)
"""

LANGSMITH_UI_JUDGE_PROMPT = """\
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

Question: {{input.question}}

Reference answer: {{referenceOutput.answer}}

Predicted answer: {{output.output.content}}"""
