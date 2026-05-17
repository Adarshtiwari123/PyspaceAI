"""
Sarvam AI STT — saarika:v2.5
Replaces OpenAI Whisper with Sarvam's Indian-language speech recognition.
Supports Hindi, English, and Hinglish (mixed).
Keeps the same function signatures as the Whisper version so nothing
else in your codebase needs to change.
"""
import os
import io
import requests
from dotenv import load_dotenv

load_dotenv()

SARVAM_KEY = os.getenv("SARVAM_AI") or os.getenv("SARVAM_API_KEY", "")
STT_URL    = "https://api.sarvam.ai/speech-to-text"

# ── Language options ──────────────────────────────────────────────────────────
# "en-IN" → English (Indian accent)
# "hi-IN" → Hindi
# "unknown" → Sarvam auto-detects (good for Hinglish)
DEFAULT_LANGUAGE = "unknown"   # auto-detect Hindi/English/Hinglish


def _detect_format(raw: bytes) -> str:
    """Detect audio format from magic bytes — browsers record webm, not wav."""
    if raw[:4] == b'RIFF':               return "wav"
    if raw[:4] == b'fLaC':              return "flac"
    if raw[:3] in (b'ID3', b'\xff\xfb'): return "mp3"
    if raw[4:8] == b'ftyp':             return "mp4"
    if raw[:4] == b'\x1a\x45\xdf\xa3':  return "webm"
    if raw[:4] == b'OggS':              return "ogg"
    return "webm"   # safe default for all modern browsers


def transcribe_audio(audio_input, language: str = DEFAULT_LANGUAGE) -> str:
    """
    Transcribe voice using Sarvam saarika:v2.5.
    Drop-in replacement for the Whisper version — same signature.

    audio_input : UploadedFile / BytesIO from st.audio_input()
    language    : BCP-47 code or "unknown" for auto-detect
    Returns     : transcribed string, or "" on failure
    """
    text, _ = transcribe_audio_debug(audio_input, language)
    return text


def transcribe_audio_debug(
    audio_input,
    language: str = DEFAULT_LANGUAGE,
) -> tuple[str, str]:
    """
    Returns (transcribed_text, debug_message).
    debug_message is "ok" on success, error description on failure.
    Same signature as the Whisper version.
    """
    if not SARVAM_KEY:
        return "", "SARVAM_AI key not set in .env"

    # ── Read raw bytes ────────────────────────────────────────────
    try:
        if hasattr(audio_input, "getvalue"):
            raw = audio_input.getvalue()
        elif hasattr(audio_input, "read"):
            try:
                audio_input.seek(0)
            except Exception:
                pass
            raw = audio_input.read()
        else:
            raw = bytes(audio_input)
    except Exception as e:
        return "", f"Failed to read audio bytes: {e}"

    if not raw:
        return "", "No audio data received — mic may not have recorded"
    if len(raw) < 500:
        return "", f"Audio too short ({len(raw)} bytes) — try speaking longer"

    # ── Detect format ─────────────────────────────────────────────
    fmt = _detect_format(raw)
    mime_map = {
        "wav":  "audio/wav",
        "webm": "audio/webm",
        "ogg":  "audio/ogg",
        "mp3":  "audio/mpeg",
        "mp4":  "audio/mp4",
        "flac": "audio/flac",
    }
    mime = mime_map.get(fmt, "audio/webm")

    # ── Sarvam STT API call ───────────────────────────────────────
    try:
        files = {
            "file": (f"recording.{fmt}", io.BytesIO(raw), mime),
        }
        data = {
            "model":            "saarika:v2.5",
            "language_code":    language,      # "unknown" = auto-detect
            "with_timestamps":  "false",
        }

        resp = requests.post(
            STT_URL,
            headers={"api-subscription-key": SARVAM_KEY},
            files=files,
            data=data,
            timeout=30,
        )
        resp.raise_for_status()

        transcript = resp.json().get("transcript", "").strip()

        if not transcript:
            return "", "Sarvam returned empty transcript — no speech detected"

        print(f"[Sarvam STT] Transcribed ({fmt}, {len(raw)}B): '{transcript[:120]}'")
        return transcript, "ok"

    except requests.exceptions.HTTPError as e:
        detail = e.response.text[:300] if e.response else str(e)
        return "", f"Sarvam STT HTTP {e.response.status_code}: {detail}"
    except Exception as e:
        return "", f"{type(e).__name__}: {e}"
