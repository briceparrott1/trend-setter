"""Video generation via Kling AI + OpenAI TTS + FFmpeg assembly."""

from __future__ import annotations

import asyncio
import datetime
import logging
import re
import time
from pathlib import Path

import httpx

from trend_setter.config import Settings
from trend_setter.generation.tts import generate_voiceover

logger = logging.getLogger(__name__)

KLING_TEXT2VIDEO_URL = "{base}/v1/videos/text2video"
KLING_TASK_URL = "{base}/v1/videos/text2video/{task_id}"

MAX_CONCURRENT_KLING_REQUESTS = 3


async def generate_clip(
    shot_description: str,
    output_path: Path,
    settings: Settings,
    max_wait_seconds: int = 600,
) -> Path:
    """Generate a single video clip via Kling AI text-to-video.

    Args:
        shot_description: One-sentence cinematic shot description.
        output_path: Where to save the downloaded MP4.
        settings: App settings (kling_api_key, kling_clip_duration, etc.).
        max_wait_seconds: Timeout for polling task completion.

    Returns:
        Path to the downloaded MP4 clip.

    Raises:
        RuntimeError: If the task fails or times out.
        httpx.HTTPError: On API errors.
    """
    headers = {
        "Authorization": f"Bearer {settings.kling_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model_name": "kling-v1",
        "prompt": f"{settings.kling_style_prefix} {shot_description}",
        "negative_prompt": settings.kling_negative_prompt,
        "duration": str(settings.kling_clip_duration),
        "aspect_ratio": "9:16",  # vertical for Reels
        "mode": "std",  # standard quality
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            KLING_TEXT2VIDEO_URL.format(base=settings.kling_api_base),
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        task_data = response.json()
        task_id = task_data["data"]["task_id"]

        start = time.monotonic()
        while True:
            if time.monotonic() - start > max_wait_seconds:
                raise RuntimeError(
                    f"Kling task {task_id} timed out after {max_wait_seconds}s"
                )

            await asyncio.sleep(5)

            status_response = await client.get(
                KLING_TASK_URL.format(base=settings.kling_api_base, task_id=task_id),
                headers=headers,
            )
            status_response.raise_for_status()
            status_data = status_response.json()
            task_status = status_data["data"]["task_status"]

            if task_status == "succeed":
                video_url = status_data["data"]["task_result"]["videos"][0]["url"]
                break
            elif task_status == "failed":
                reason = status_data["data"].get("task_status_msg", "unknown")
                raise RuntimeError(f"Kling task {task_id} failed: {reason}")
            # "processing" or "submitted" — keep polling

        video_response = await client.get(video_url)
        video_response.raise_for_status()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(video_response.content)
        return output_path


async def generate_all_clips(
    shot_descriptions: list[str],
    output_dir: Path,
    settings: Settings,
) -> list[Path]:
    """Generate all clips in parallel (with concurrency limit to avoid rate limits).

    A clip that raises (e.g. a Kling timeout) is retried once before being
    counted as a permanent failure. A single permanent failure does not
    fail the whole batch as long as at least half of the requested clips
    (``min_clips``) succeed.

    Returns:
        List of paths to downloaded MP4 clips, in the order their tasks
        completed (failed clips are dropped).

    Raises:
        RuntimeError: If fewer than ``min_clips`` clips succeeded.
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_KLING_REQUESTS)

    async def _generate_one(idx: int, description: str) -> Path:
        async with semaphore:
            clip_path = output_dir / f"clip_{idx:02d}.mp4"
            try:
                return await generate_clip(description, clip_path, settings)
            except (RuntimeError, httpx.HTTPError) as e:
                logger.warning("clip %d failed (%s), retrying once...", idx, e)
                return await generate_clip(description, clip_path, settings)

    tasks = [
        _generate_one(i, desc)
        for i, desc in enumerate(shot_descriptions[: settings.kling_clips_per_video])
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    clip_paths = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error("clip %d failed permanently: %s", i, r)
        else:
            clip_paths.append(r)

    min_clips = max(1, settings.kling_clips_per_video // 2)
    if len(clip_paths) < min_clips:
        raise RuntimeError(
            f"Only {len(clip_paths)}/{len(results)} clips succeeded "
            f"(minimum {min_clips})"
        )
    return clip_paths


def _split_script_into_captions(script: str) -> list[str]:
    """Split narration into caption-sized segments on sentence/clause breaks."""
    segments = re.split(r"(?<=[.!?,])\s+", script.strip())
    return [segment.strip() for segment in segments if segment.strip()]


def _estimate_caption_segments(
    script: str, duration: float
) -> list[tuple[str, float, float]]:
    """Estimate (text, start, end) timing for each caption segment.

    OpenAI TTS returns no word-level alignment data, so timing is estimated
    by distributing `duration` across segments proportional to each
    segment's word count. This is "good enough" sync, not exact alignment.
    """
    segments = _split_script_into_captions(script)
    if not segments or duration <= 0:
        return []

    word_counts = [max(len(segment.split()), 1) for segment in segments]
    total_words = sum(word_counts)

    timed_segments = []
    t = 0.0
    for segment, words in zip(segments, word_counts, strict=True):
        seg_duration = duration * words / total_words
        timed_segments.append((segment, t, t + seg_duration))
        t += seg_duration
    return timed_segments


def _build_subtitle_clips(
    script: str, duration: float, video_size: tuple[int, int]
) -> list:
    """Build burned-in caption TextClips, styled for legibility on a phone screen.

    High-contrast white text with a black stroke, positioned in the lower-
    middle area (clear of Instagram's own UI chrome, which occupies the
    very bottom and top of the frame). `video_size` is the actual assembled
    video's (width, height) — captions are sized/positioned relative to it
    so they stay on-screen regardless of Kling's true output resolution.
    """
    from moviepy.editor import TextClip

    width, _height = video_size
    clips = []
    for text, start, end in _estimate_caption_segments(script, duration):
        clip = (
            TextClip(
                text,
                fontsize=58,
                color="white",
                font="Arial-Bold",
                stroke_color="black",
                stroke_width=3,
                method="caption",
                size=(int(width * 0.9), None),
                align="center",
            )
            .set_start(start)
            .set_duration(end - start)
            .set_position(("center", 0.7), relative=True)
        )
        clips.append(clip)
    return clips


def assemble_video(
    clip_paths: list[Path],
    voiceover_path: Path,
    output_path: Path,
    script: str,
) -> Path:
    """Assemble clips + voiceover + burned-in captions into a final MP4 using moviepy.

    - Concatenates all clips in order.
    - Lays the voiceover audio over the full video.
    - Trims (or loops the last clip) to match voiceover duration.
    - Burns in caption text derived from `script`, timed proportionally
      across the final (voiceover-matched) duration.
    - Outputs a 9:16 vertical MP4.

    Returns:
        Path to the assembled video.
    """
    from moviepy.editor import (
        AudioFileClip,
        CompositeVideoClip,
        VideoFileClip,
        concatenate_videoclips,
    )

    clips = [VideoFileClip(str(p)) for p in clip_paths]
    video = concatenate_videoclips(clips, method="compose")
    audio = AudioFileClip(str(voiceover_path))

    if video.duration < audio.duration:
        from moviepy.editor import vfx

        extra = audio.duration - video.duration + clips[-1].duration
        last = clips[-1].fx(vfx.loop, duration=extra)
        video = concatenate_videoclips(clips[:-1] + [last], method="compose")
    else:
        video = video.subclip(0, audio.duration)

    subtitle_clips = _build_subtitle_clips(script, audio.duration, video.size)
    if subtitle_clips:
        video = CompositeVideoClip([video, *subtitle_clips])

    final = video.set_audio(audio)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final.write_videofile(
        str(output_path),
        codec="libx264",
        audio_codec="aac",
        fps=24,
        logger=None,  # suppress moviepy progress bars in production
    )

    for clip in clips:
        clip.close()
    audio.close()
    final.close()

    return output_path


async def generate_video(
    shot_descriptions: list[str],
    script: str,
    output_dir: Path,
    settings: Settings,
) -> Path:
    """Full video generation: TTS + Kling clips + assembly.

    Args:
        shot_descriptions: Cinematic shot descriptions from the brief (one
            per clip).
        script: Full narration text for TTS.
        output_dir: Directory to write intermediate and final files.
        settings: App settings.

    Returns:
        Path to the final assembled MP4.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    clips_dir = output_dir / f"clips_{timestamp}"
    voiceover_path = output_dir / f"voiceover_{timestamp}.mp3"
    final_path = output_dir / f"trend_setter_{timestamp}.mp4"

    voiceover_path, clip_paths = await asyncio.gather(
        generate_voiceover(
            script,
            voiceover_path,
            settings.openai_api_key,
            voice=settings.tts_voice,
            speed=settings.tts_speed,
        ),
        generate_all_clips(shot_descriptions, clips_dir, settings),
    )

    return await asyncio.to_thread(
        assemble_video, clip_paths, voiceover_path, final_path, script
    )
