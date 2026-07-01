"""Unit + smoke tests for Kling AI clip generation, assembly, and orchestration."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from trend_setter.config import Settings
from trend_setter.generation.video import (
    assemble_video,
    generate_all_clips,
    generate_clip,
    generate_video,
)


@pytest.fixture
def settings() -> Settings:
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


class _FakeResponse:
    def __init__(self, json_data=None, content: bytes = b"") -> None:
        self._json_data = json_data
        self.content = content

    def raise_for_status(self) -> None:
        pass

    def json(self):
        return self._json_data


class _FakeAsyncClient:
    def __init__(self, post_response, get_responses: list) -> None:
        self.post = AsyncMock(return_value=post_response)
        self.get = AsyncMock(side_effect=get_responses)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False


async def test_generate_clip_polls_until_succeed_and_downloads(
    tmp_path: Path, settings: Settings
) -> None:
    post_response = _FakeResponse(json_data={"data": {"task_id": "task-1"}})
    status_response = _FakeResponse(
        json_data={
            "data": {
                "task_status": "succeed",
                "task_result": {"videos": [{"url": "https://cdn.example.com/v.mp4"}]},
            }
        }
    )
    download_response = _FakeResponse(content=b"fake-mp4-bytes")
    fake_client = _FakeAsyncClient(post_response, [status_response, download_response])

    output_path = tmp_path / "clips" / "clip_00.mp4"

    with (
        patch(
            "trend_setter.generation.video.httpx.AsyncClient",
            return_value=fake_client,
        ),
        patch(
            "trend_setter.generation.video.asyncio.sleep", new=AsyncMock()
        ) as mock_sleep,
    ):
        result = await generate_clip("a cinematic shot", output_path, settings)

    assert result == output_path
    assert output_path.read_bytes() == b"fake-mp4-bytes"
    fake_client.post.assert_called_once()
    posted_payload = fake_client.post.call_args.kwargs["json"]
    assert posted_payload["prompt"] == (
        f"{settings.kling_style_prefix} a cinematic shot"
    )
    assert posted_payload["negative_prompt"] == settings.kling_negative_prompt
    assert fake_client.get.await_count == 2
    mock_sleep.assert_awaited_once_with(5)


async def test_generate_clip_raises_on_failed_status(
    tmp_path: Path, settings: Settings
) -> None:
    post_response = _FakeResponse(json_data={"data": {"task_id": "task-1"}})
    failed_response = _FakeResponse(
        json_data={"data": {"task_status": "failed", "task_status_msg": "bad prompt"}}
    )
    fake_client = _FakeAsyncClient(post_response, [failed_response])

    with (
        patch(
            "trend_setter.generation.video.httpx.AsyncClient",
            return_value=fake_client,
        ),
        patch("trend_setter.generation.video.asyncio.sleep", new=AsyncMock()),
    ):
        with pytest.raises(RuntimeError, match="bad prompt"):
            await generate_clip("a shot", tmp_path / "clip.mp4", settings)


async def test_generate_all_clips_caps_at_clips_per_video(
    tmp_path: Path, settings: Settings
) -> None:
    shot_descriptions = [f"shot {i}" for i in range(8)]

    async def _fake_generate_clip(description, output_path, settings):
        return output_path

    with patch(
        "trend_setter.generation.video.generate_clip",
        new=AsyncMock(side_effect=_fake_generate_clip),
    ) as mock_generate_clip:
        clip_paths = await generate_all_clips(shot_descriptions, tmp_path, settings)

    assert mock_generate_clip.await_count == settings.kling_clips_per_video
    assert clip_paths == [
        tmp_path / f"clip_{i:02d}.mp4" for i in range(settings.kling_clips_per_video)
    ]


async def test_generate_all_clips_retries_failed_clip_once_and_continues(
    tmp_path: Path, settings: Settings
) -> None:
    shot_descriptions = [f"shot {i}" for i in range(6)]
    call_counts: dict[int, int] = {}

    async def _fake_generate_clip(description, output_path, settings):
        idx = int(output_path.stem.split("_")[1])
        call_counts[idx] = call_counts.get(idx, 0) + 1
        if idx == 2 and call_counts[idx] == 1:
            raise RuntimeError("Kling task timed out after 600s")
        return output_path

    with patch(
        "trend_setter.generation.video.generate_clip",
        new=AsyncMock(side_effect=_fake_generate_clip),
    ):
        clip_paths = await generate_all_clips(shot_descriptions, tmp_path, settings)

    assert call_counts[2] == 2  # failed once, succeeded on retry
    assert len(clip_paths) == 6
    assert tmp_path / "clip_02.mp4" in clip_paths


async def test_generate_all_clips_continues_when_one_clip_fails_permanently(
    tmp_path: Path, settings: Settings
) -> None:
    shot_descriptions = [f"shot {i}" for i in range(6)]

    async def _fake_generate_clip(description, output_path, settings):
        idx = int(output_path.stem.split("_")[1])
        if idx == 5:
            raise RuntimeError("Kling task timed out after 600s")
        return output_path

    with patch(
        "trend_setter.generation.video.generate_clip",
        new=AsyncMock(side_effect=_fake_generate_clip),
    ):
        clip_paths = await generate_all_clips(shot_descriptions, tmp_path, settings)

    assert len(clip_paths) == 5
    assert tmp_path / "clip_05.mp4" not in clip_paths


async def test_generate_all_clips_raises_when_too_few_clips_succeed(
    tmp_path: Path, settings: Settings
) -> None:
    shot_descriptions = [f"shot {i}" for i in range(6)]

    async def _fake_generate_clip(description, output_path, settings):
        raise RuntimeError("Kling task timed out after 600s")

    with patch(
        "trend_setter.generation.video.generate_clip",
        new=AsyncMock(side_effect=_fake_generate_clip),
    ):
        with pytest.raises(RuntimeError, match="succeeded"):
            await generate_all_clips(shot_descriptions, tmp_path, settings)


def test_assemble_video_trims_to_shorter_audio(tmp_path: Path) -> None:
    clip_paths = [tmp_path / "clip_00.mp4", tmp_path / "clip_01.mp4"]
    voiceover_path = tmp_path / "voiceover.mp3"
    output_path = tmp_path / "final.mp4"

    mock_clips = [MagicMock(duration=5.0) for _ in clip_paths]
    mock_video = MagicMock(duration=10.0)
    mock_trimmed = MagicMock()
    mock_video.subclip.return_value = mock_trimmed
    mock_final = MagicMock()
    mock_trimmed.set_audio.return_value = mock_final
    mock_audio = MagicMock(duration=6.0)

    with (
        patch(
            "moviepy.editor.VideoFileClip", side_effect=mock_clips
        ) as mock_video_file_clip,
        patch(
            "moviepy.editor.concatenate_videoclips", return_value=mock_video
        ) as mock_concat,
        patch("moviepy.editor.AudioFileClip", return_value=mock_audio),
    ):
        result = assemble_video(clip_paths, voiceover_path, output_path)

    mock_video_file_clip.assert_any_call(str(clip_paths[0]))
    mock_video_file_clip.assert_any_call(str(clip_paths[1]))
    mock_concat.assert_called_once_with(mock_clips, method="compose")
    mock_video.subclip.assert_called_once_with(0, 6.0)
    mock_trimmed.set_audio.assert_called_once_with(mock_audio)
    mock_final.write_videofile.assert_called_once_with(
        str(output_path),
        codec="libx264",
        audio_codec="aac",
        fps=24,
        logger=None,
    )
    assert result == output_path


def test_assemble_video_loops_last_clip_when_audio_longer(tmp_path: Path) -> None:
    clip_paths = [tmp_path / "clip_00.mp4", tmp_path / "clip_01.mp4"]
    voiceover_path = tmp_path / "voiceover.mp3"
    output_path = tmp_path / "final.mp4"

    mock_clips = [MagicMock(duration=5.0), MagicMock(duration=5.0)]
    mock_looped_last = MagicMock()
    mock_clips[1].fx.return_value = mock_looped_last
    mock_video_short = MagicMock(duration=10.0)
    mock_video_extended = MagicMock()
    mock_final = MagicMock()
    mock_video_extended.set_audio.return_value = mock_final
    mock_audio = MagicMock(duration=20.0)

    with (
        patch("moviepy.editor.VideoFileClip", side_effect=mock_clips),
        patch(
            "moviepy.editor.concatenate_videoclips",
            side_effect=[mock_video_short, mock_video_extended],
        ) as mock_concat,
        patch("moviepy.editor.AudioFileClip", return_value=mock_audio),
    ):
        result = assemble_video(clip_paths, voiceover_path, output_path)

    mock_clips[1].fx.assert_called_once()
    assert mock_concat.call_count == 2
    mock_video_extended.set_audio.assert_called_once_with(mock_audio)
    assert result == output_path


async def test_generate_video_orchestrates_tts_clips_and_assembly(
    tmp_path: Path, settings: Settings
) -> None:
    shot_descriptions = [f"shot {i}" for i in range(6)]
    script = "Did you know octopuses have three hearts?"
    clip_paths = [tmp_path / f"clip_{i:02d}.mp4" for i in range(6)]
    final_path = tmp_path / "final.mp4"

    with (
        patch(
            "trend_setter.generation.video.generate_voiceover",
            new=AsyncMock(side_effect=lambda script, output_path, api_key: output_path),
        ) as mock_tts,
        patch(
            "trend_setter.generation.video.generate_all_clips",
            new=AsyncMock(return_value=clip_paths),
        ) as mock_clips,
        patch(
            "trend_setter.generation.video.assemble_video",
            return_value=final_path,
        ) as mock_assemble,
    ):
        result = await generate_video(shot_descriptions, script, tmp_path, settings)

    assert result == final_path
    mock_tts.assert_awaited_once()
    assert mock_tts.await_args.args[0] == script
    assert mock_tts.await_args.args[2] == settings.openai_api_key

    mock_clips.assert_awaited_once()
    clips_call_args = mock_clips.await_args.args
    assert clips_call_args[0] == shot_descriptions
    assert clips_call_args[1].parent == tmp_path
    assert clips_call_args[1].name.startswith("clips_")
    assert clips_call_args[2] == settings

    mock_assemble.assert_called_once()
    assert mock_assemble.call_args.args[0] == clip_paths
