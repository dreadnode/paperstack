from openai import OpenAI

from _types import Focus

OpenAIClient = OpenAI

SUMMARIZE_ABSTRACT_PROMPT = """\
You will be provided with an abstract of a scientific paper. \
Compress this abstract in 1-2 sentences. Use very concise language usable as \
bullet points on a slide deck. Respond ONLY with your summary.
"""

ASSIGN_LABEL_PROMPT = """\
You will be provided with an abstract of a scientific paper. \
Assess the most applicable focus label based on the target audience, \
research focus, produced materials, and key outcomes.

{labels}

Respond with ONLY ONE of the labels above. Do not include anything else in your response.
"""

def get_openai_client(token: str) -> OpenAIClient:
    return OpenAI(api_key=token)


def summarize_abstract_with_openai(client: OpenAIClient, abstract: str) -> str:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": SUMMARIZE_ABSTRACT_PROMPT},
            {"role": "user", "content": f"{abstract}"},
        ],
        temperature=0.5,
        max_tokens=100,
    )

    return response.choices[0].message.content.strip() # type: ignore

def get_focus_label_from_abstract(client: OpenAIClient, abstract: str) -> Focus | None:
    system_prompt = ASSIGN_LABEL_PROMPT.format(
        labels="\n".join([f"- {f.value}" for f in Focus])
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{abstract}"},
        ],
        temperature=0.5,
        max_tokens=10,
    )

    content = response.choices[0].message.content.strip() # type: ignore
    if content not in [f.value for f in Focus]:
        return None
    
    return Focus(content)