"""Text-to-speech via OpenAI TTS API."""

from __future__ import annotations

import asyncio
from pathlib import Path

import openai


async def generate_voiceover(
    script: str,
    output_path: Path,
    api_key: str,
    model: str = "tts-1",
    voice: str = "nova",
) -> Path:
    """Generate a voiceover MP3 from a script using OpenAI TTS.

    Args:
        script: Full narration text (60-85 words).
        output_path: Where to write the MP3 file.
        api_key: OpenAI API key.
        model: TTS model ('tts-1' for speed, 'tts-1-hd' for quality).
        voice: Voice name ('nova' is clear and neutral; alternatives:
            alloy, echo, fable, onyx, shimmer).

    Returns:
        Path to the generated MP3 file.
    """

    def _generate() -> Path:
        client = openai.OpenAI(api_key=api_key)
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=script,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        response.stream_to_file(str(output_path))
        return output_path

    return await asyncio.to_thread(_generate)
