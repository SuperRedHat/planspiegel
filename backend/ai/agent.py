from typing import List

from openai import OpenAI

from ai.generate_checks_embeddings import docs_by_check_type
from constants import OPENAI_API_KEY
from models import Message, CheckType

client = OpenAI(api_key=OPENAI_API_KEY)


def create_system_prompt(results: str, check_type: CheckType) -> dict[str, str]:
    docs = docs_by_check_type[check_type]
    # f"If user question is a random text or doesn't make sense, "
    # f"comment it in a witty way and provide 3 practical examples of questions.
    return {
        "role": "system",
        "content": (
            f"You are a helpful cybersecurity assistant, you always use security standards in your answers. "
            f"Ask questions to the user if needed. "
            f"You have check descriptions:\n{docs}\n"
            f"Analyze the following security check results and suggest solutions:\n{results}"
        )
    }


def create_context_messages(system_message: dict[str, str], messages_from_db: List[Message], question: str,
                            attachment_url: str | None):
    messages = [system_message]
    for message in messages_from_db:
        messages.append({"role": message.sender_type.value, "content": message.content})

    # ATTACHMENT
    # "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
    # If yes switch from Google Cloud to local storage Minio (or store base64 in postgres)

    if attachment_url is not None:
        messages.append({"role": "user", "content": [
            {"type": "text", "text": question},
            {"type": "image_url", "image_url": {"url": attachment_url}}
        ]})
    else:
        messages.append({"role": "user", "content": question})

    return messages


def get_agent_response(check_type: CheckType, results: str, messages, question: str, attachment_url: str | None):
    prompt = create_system_prompt(results, check_type)
    messages = create_context_messages(prompt, messages, question, attachment_url)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=False
    )
    return response.choices[0].message.content


def get_agent_response_stream(check_type: CheckType, results: str, messages, question: str, attachment_url: str | None):
    prompt = create_system_prompt(results, check_type)
    messages = create_context_messages(prompt, messages, question, attachment_url)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=True
    )

    for chunk in response:
        yield chunk.choices[0].delta.content


def trim_results(results: str, max_length: int = 4000) -> str:
    return results[:max_length] + "..." if len(results) > max_length else results


def get_agent_check_summary_response(results: str, check_type: CheckType):
    prompt = create_system_prompt(results, check_type)
    summary_prompt = f"Make 1 paragraph (maximum 150 words) of summary for check results"
    messages = [prompt, {"role": "user", "content": summary_prompt}]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=False
    )
    return response.choices[0].message.content
