"""Unit tests for OpenAI TTS voiceover generation."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from trend_setter.generation.tts import generate_voiceover


async def test_generate_voiceover_writes_mp3(tmp_path: Path) -> None:
    output_path = tmp_path / "voiceover" / "out.mp3"
    mock_response = MagicMock()
    mock_client = MagicMock()
    mock_client.audio.speech.create.return_value = mock_response

    with patch(
        "trend_setter.generation.tts.openai.OpenAI", return_value=mock_client
    ) as mock_openai:
        result = await generate_voiceover(
            script="Did you know octopuses have three hearts?",
            output_path=output_path,
            api_key="test-key",
        )

    mock_openai.assert_called_once_with(api_key="test-key")
    mock_client.audio.speech.create.assert_called_once_with(
        model="tts-1",
        voice="nova",
        input="Did you know octopuses have three hearts?",
    )
    mock_response.stream_to_file.assert_called_once_with(str(output_path))
    assert result == output_path
    assert output_path.parent.is_dir()


async def test_generate_voiceover_uses_custom_model_and_voice(tmp_path: Path) -> None:
    output_path = tmp_path / "out.mp3"
    mock_response = MagicMock()
    mock_client = MagicMock()
    mock_client.audio.speech.create.return_value = mock_response

    with patch("trend_setter.generation.tts.openai.OpenAI", return_value=mock_client):
        await generate_voiceover(
            script="script text",
            output_path=output_path,
            api_key="test-key",
            model="tts-1-hd",
            voice="alloy",
        )

    mock_client.audio.speech.create.assert_called_once_with(
        model="tts-1-hd",
        voice="alloy",
        input="script text",
    )
