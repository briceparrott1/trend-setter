"""Unit tests for Gemini brief/script prompt construction.

The hook-attribution guardrail (ATTRIBUTED vs. NON-ATTRIBUTED hook choice)
is a model-judgment call, not something deterministically verifiable here —
see AGENTS.md. These tests only check the prompt text itself and that
generate_brief feeds enough raw research context into it for that judgment
to be possible.
"""

import json
from unittest.mock import MagicMock, patch

from trend_setter.config import Settings
from trend_setter.generation.brief import SCRIPT_PROMPT, generate_brief


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        instagram_access_token="token",
        instagram_account_id="acct",
        gemini_api_key="gemini-key",
        kling_api_key="kling-key",
        perplexity_api_key="perplexity-key",
        youtube_api_key="yt-key",
        newsdataio_api_key="newsdataio-key",
        openai_api_key="openai-key",
    )


def test_script_prompt_describes_both_hook_branches_and_drops_no_people() -> None:
    assert "ATTRIBUTED" in SCRIPT_PROMPT
    assert "NON-ATTRIBUTED" in SCRIPT_PROMPT
    assert "no people" not in SCRIPT_PROMPT.lower()
    assert "actively" in SCRIPT_PROMPT.lower()
    assert "no on-screen text" in SCRIPT_PROMPT.lower()


async def test_generate_brief_passes_raw_research_notes_to_prompt() -> None:
    research = {
        "hook_fact": "Octopuses have three hearts.",
        "supporting_facts": ["Two pump blood to the gills."],
        "citations": ["https://example.com"],
        "raw_answer": "Dr. Jane Smith says octopuses are remarkable.",
        "wikipedia": {"extract": "An octopus is a soft-bodied mollusc."},
    }
    mock_response = MagicMock()
    mock_response.text = json.dumps(
        {
            "script": "Did you know...",
            "shot_descriptions": [f"shot {i}" for i in range(6)],
            "caption": "caption",
            "hashtags": ["#tag"],
        }
    )
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response

    with (
        patch(
            "trend_setter.generation.brief.genai.GenerativeModel",
            return_value=mock_model,
        ),
        patch("trend_setter.generation.brief.genai.configure"),
    ):
        await generate_brief("octopus hearts", research, _settings())

    prompt = mock_model.generate_content.call_args.args[0]
    assert "Dr. Jane Smith says octopuses are remarkable." in prompt
    assert "An octopus is a soft-bodied mollusc." in prompt


async def test_generate_brief_handles_missing_research_notes() -> None:
    research = {"citations": []}
    mock_response = MagicMock()
    mock_response.text = json.dumps(
        {
            "script": "Did you know...",
            "shot_descriptions": [f"shot {i}" for i in range(6)],
            "caption": "caption",
            "hashtags": ["#tag"],
        }
    )
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response

    with (
        patch(
            "trend_setter.generation.brief.genai.GenerativeModel",
            return_value=mock_model,
        ),
        patch("trend_setter.generation.brief.genai.configure"),
    ):
        result = await generate_brief("octopus hearts", research, _settings())

    prompt = mock_model.generate_content.call_args.args[0]
    assert "No additional research notes." in prompt
    assert result["script"] == "Did you know..."
