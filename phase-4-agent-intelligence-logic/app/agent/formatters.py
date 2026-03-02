"""
Channel-specific response formatters.
Adapts agent output to match channel conventions discovered during incubation.
"""


def format_response_for_channel(response: str, channel: str) -> str:
    """
    Format agent response based on target channel.

    Args:
        response: Raw agent response text
        channel: Target channel (email, whatsapp, web_form)

    Returns:
        Formatted response appropriate for the channel
    """
    if channel == "email":
        return format_email_response(response)
    elif channel == "whatsapp":
        return format_whatsapp_response(response)
    elif channel == "web_form":
        return format_webform_response(response)
    return response


def format_email_response(response: str) -> str:
    """
    Format response for email channel.
    - Formal tone, detailed
    - Includes greeting and signature
    - Max 500 words
    """
    words = response.split()
    if len(words) > 500:
        response = " ".join(words[:500]) + "..."

    # Add greeting if not present
    greetings = ["dear", "hello", "hi ", "good morning", "good afternoon"]
    has_greeting = any(response.lower().startswith(g) for g in greetings)

    if not has_greeting:
        response = f"Hello,\n\n{response}"

    # Add signature if not present
    if "best regards" not in response.lower() and "sincerely" not in response.lower():
        response += "\n\nBest regards,\nTechCorp Customer Success Team"

    return response


def format_whatsapp_response(response: str) -> str:
    """
    Format response for WhatsApp channel.
    - Conversational, concise
    - Keep under 300 characters when possible
    - Use simple language
    """
    # Remove formal elements
    response = response.replace("Best regards,\nTechCorp Customer Success Team", "")
    response = response.replace("Hello,\n\n", "")
    response = response.replace("Dear Customer,\n\n", "")

    # Trim to 300 chars if possible, break at sentence
    if len(response) > 300:
        sentences = response.split(". ")
        trimmed = ""
        for s in sentences:
            if len(trimmed) + len(s) + 2 <= 300:
                trimmed += s + ". "
            else:
                break
        if trimmed:
            response = trimmed.strip()
        else:
            response = response[:297] + "..."

    return response.strip()


def format_webform_response(response: str) -> str:
    """
    Format response for web form channel.
    - Semi-formal, helpful
    - Max 300 words
    - Clean formatting
    """
    words = response.split()
    if len(words) > 300:
        response = " ".join(words[:300]) + "..."

    # Remove email-style signatures
    response = response.replace("Best regards,\nTechCorp Customer Success Team", "")

    return response.strip()
