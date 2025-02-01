from _types import AttackType, Focus
from openai import OpenAI

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

# Attack Type descriptions

EVASION_DESCRIPTION = """\
Model Evasion is an adversarial attack aimed at bypassing or evading a machine 
learning model's defenses, usually to make it produce incorrect outputs or behave 
in ways that favor the attacker. In this context, the adversary doesn't try to 
"break" the model or extract data from it (like in model inversion) but instead 
seeks to manipulate the model's behavior in a way that allows them to achieve a 
desired outcome, such as bypassing detection systems or generating misleading predictions.
"""

EXTRACTION_DESCRIPTION = """\
Model Extraction refers to an attack where an adversary tries to replicate or steal 
the functionality of a machine learning model by querying it and using the outputs 
to build a copy of the original model. This type of attack doesn't necessarily involve 
extracting sensitive data used for training, as in model inversion, but instead focuses 
on how the model behaves—its predictions and outputs—in order to create a surrogate or 
shadow model that behaves similarly to the original.
"""

INVERSION_DESCRIPTION = """\
Model inversion refers to a set of techniques in machine learning where an attacker
tries to extract confidential information from a trained AI model by interacting with
it in specific ways, often through extensive querying. By doing so, the attacker may
be able to infer details about the data used to train the model. These details can
range from personal information to the reconstruction of private or sensitive datasets,
potentially revealing confidential information.
"""

POISONING_DESCRIPTION = """\
Model Poisoning is an attack on machine learning models where an adversary intentionally
manipulates data in the training set to impact how a model behaves. Unlike attacks like
model inversion or model extraction, which focus on extracting information from the model,
model poisoning targets the model during its training phase. By introducing misleading,
incorrect, or adversarial data, attackers can manipulate a model's behavior, often without
detection, leading to significant security, reliability, and ethical risks.
"""

PROMPT_INJECTION_DESCRIPTION = """\
Prompt injection is a critical vulnerability in Large Language Models (LLMs), where malicious
users manipulate model behavior by crafting inputs that override, bypass, or exploit how the
model follows instructions. This vulnerability has become more pronounced with the widespread
use of generative AI systems, enabling attackers to induce unintended responses that may lead
to data leakage, misinformation, or system disruptions.
"""


ATTACK_TYPE_DESCRIPTIONS: dict[AttackType, str] = {
    AttackType.ModelEvasion: EVASION_DESCRIPTION,
    AttackType.ModelExtraction: EXTRACTION_DESCRIPTION,
    AttackType.ModelInversion: INVERSION_DESCRIPTION,
    AttackType.ModelPoisoning: POISONING_DESCRIPTION,
    AttackType.PromptInjection: PROMPT_INJECTION_DESCRIPTION,
    AttackType.Other: "None of the above",
}

ASSIGN_ATTACK_TYPE_PROMPT = """\
You will be provided with an abstract of a scientific paper. \
Assess the most applicable attack type label based on the \
research focus, produced materials, and key outcomes.

{types}

If you feel like none of the types apply, you can respond with "Other".

Respond with ONLY ONE of the labels above. Do not include anything else in your response.
"""

# Model Evasion
# Model Extraction
# Model Inversion
# Model Poisoning
# Prompt Injection

def get_openai_client(token: str) -> OpenAIClient:
    return OpenAI(api_key=token)


def summarize_abstract_with_openai(client: OpenAIClient, abstract: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SUMMARIZE_ABSTRACT_PROMPT},
            {"role": "user", "content": f"{abstract}"},
        ],
        temperature=0.5,
        max_tokens=100,
    )

    return response.choices[0].message.content.strip()  # type: ignore


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

    content = response.choices[0].message.content.strip()  # type: ignore
    if content not in [f.value for f in Focus]:
        return None

    return Focus(content)

def get_attack_type_from_abstract(client: OpenAIClient, abstract: str) -> AttackType | None:
    system_prompt = ASSIGN_ATTACK_TYPE_PROMPT.format(
        types="\n".join([f"- `{t.value}`: {ATTACK_TYPE_DESCRIPTIONS[t]}" for t in AttackType])
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

    content = response.choices[0].message.content.strip()  # type: ignore
    content = content.strip("`")

    if content not in [t.value for t in AttackType]:
        print(f"Invalid attack type: {content}")
        return None

    return AttackType(content)