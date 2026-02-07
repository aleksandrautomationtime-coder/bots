# -*- coding: utf-8 -*-
"""Транскрипт YouTube по ссылке (для бота)."""
import re


def extract_video_id(url_or_id: str) -> str | None:
    s = (url_or_id or "").strip()
    if not s:
        return None
    if re.match(r"^[a-zA-Z0-9_-]{11}$", s):
        return s
    patterns = [
        r"(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})",
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/v/)([a-zA-Z0-9_-]{11})",
        r"[?&]v=([a-zA-Z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, s)
        if m:
            return m.group(1)
    return None


def get_transcript(url_or_id: str, languages: list[str] | None = None) -> str:
    video_id = extract_video_id(url_or_id)
    if not video_id:
        return ""

    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable,
    )

    lang_list = languages or ["ru", "en"]
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=lang_list)
        parts = [snippet.text for snippet in fetched]
        return " ".join(parts).strip()
    except AttributeError:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=lang_list)
            parts = [item["text"] for item in transcript]
            return " ".join(parts).strip()
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
            raise
        except Exception as e:
            return f"[Ошибка: {e}]"
    except TranscriptsDisabled:
        return "[У этого видео отключены субтитры]"
    except NoTranscriptFound:
        return "[Транскрипт для выбранного языка не найден]"
    except VideoUnavailable:
        return "[Видео недоступно или удалено]"
    except Exception as e:
        return f"[Ошибка: {e}]"
