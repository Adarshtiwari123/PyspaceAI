"""
interview/speech_to_text.py
<<<<<<< HEAD
Transcribes user voice via OpenAI Whisper.
Detects actual browser audio format (webm/wav/ogg) from magic bytes.
"""
import os
import io
from openai import OpenAI, OpenAIError
=======
Sarvam AI STT — saarika:v2.5
Replaces OpenAI Whisper with Sarvam's Indian-language speech recognition.
Supports Hindi, English, and Hinglish (mixed).
Keeps the same function signatures as the Whisper version so nothing
else in your codebase needs to change.
"""
import os
import io
import requests
>>>>>>> 4d0e189f (first update)
from dotenv import load_dotenv

load_dotenv()

<<<<<<< HEAD

def _get_client() -> OpenAI:
    try:
        import streamlit as st
        key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        key = None
    if not key:
        key = os.getenv("OPENAI_API_KEY")
    return OpenAI(api_key=key)


def _detect_format(raw: bytes) -> str:
    """Detect audio format from magic bytes — browsers record webm, not wav."""
    if raw[:4] == b'RIFF':              return "wav"
    if raw[:4] == b'fLaC':             return "flac"
    if raw[:3] in (b'ID3', b'\xff\xfb'): return "mp3"
    if raw[4:8] == b'ftyp':            return "mp4"
    if raw[:4] == b'\x1a\x45\xdf\xa3': return "webm"   # Chrome / Firefox
    if raw[:4] == b'OggS':             return "ogg"
    return "webm"   # safe default for all modern browsers


def transcribe_audio(audio_input) -> str:
    """Returns transcribed text or empty string."""
    text, _ = transcribe_audio_debug(audio_input)
    return text


def transcribe_audio_debug(audio_input) -> tuple[str, str]:
    """
    Returns (transcribed_text, debug_message).
    debug_message is "ok" on success, error description on failure.
=======
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
>>>>>>> 4d0e189f (first update)
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
<<<<<<< HEAD
        # ── Read raw bytes ──────────────────────────────────
=======
>>>>>>> 4d0e189f (first update)
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
<<<<<<< HEAD

        if not raw:
            return "", "No audio data received — mic may not have recorded"

        size = len(raw)
        if size < 500:
            return "", f"Audio too short ({size} bytes) — try speaking longer"

        # ── Detect format ────────────────────────────────────
        fmt = _detect_format(raw)

        # ── Build buffer with correct extension ──────────────
        buf = io.BytesIO(raw)
        buf.name = f"recording.{fmt}"

        # ── Whisper API call ─────────────────────────────────
        client = _get_client()
        result = client.audio.transcriptions.create(
            model    = "whisper-1",
            file     = buf,
            language = "en"
        )

        text = (result.text or "").strip()
        if not text:
            return "", "Whisper returned empty — no speech detected in recording"

        return text, "ok"

    except OpenAIError as e:
        return "", f"OpenAI error: {e}"
    except Exception as e:
        return "", f"{type(e).__name__}: {e}"

# """
# interview/speech_to_text.py
# Transcribes user voice via OpenAI Whisper.

# Root cause of "Could not transcribe" bug:
#   - Browsers (Chrome/Firefox) record audio as .webm (not .wav)
#   - We were naming the buffer "recording.wav" → Whisper rejected it
#   - Fix: detect actual format from file header bytes, use correct extension
# """
# import os
# import io
# from openai import OpenAI, OpenAIError
# from dotenv import load_dotenv

# load_dotenv()


# def _get_client() -> OpenAI:
#     try:
#         import streamlit as st
#         key = st.secrets.get("OPENAI_API_KEY")
#     except Exception:
#         key = None
#     if not key:
#         key = os.getenv("OPENAI_API_KEY")
#     return OpenAI(api_key=key)


# def _detect_format(raw: bytes) -> str:
#     """
#     Detect audio format from file header magic bytes.
#     Returns the correct file extension for Whisper.
#     """
#     if raw[:4] == b'RIFF':
#         return "wav"
#     if raw[:4] == b'fLaC':
#         return "flac"
#     if raw[:3] == b'ID3' or raw[:2] == b'\xff\xfb':
#         return "mp3"
#     if raw[4:8] == b'ftyp':
#         return "mp4"
#     # WebM / Matroska — most browsers record this format
#     if raw[:4] == b'\x1a\x45\xdf\xa3':
#         return "webm"
#     if raw[:3] == b'OggS':
#         return "ogg"
#     # Default fallback — webm is most common from browsers
#     return "webm"


# def transcribe_audio(audio_input) -> str:
#     """
#     Transcribe voice using Whisper.
#     audio_input: UploadedFile from st.audio_input()
#     Returns: transcribed text string, or "" on failure.
#     """
#     try:
#         # Step 1 — read raw bytes from UploadedFile
#         if hasattr(audio_input, "getvalue"):
#             raw = audio_input.getvalue()
#         elif hasattr(audio_input, "read"):
#             audio_input.seek(0)
=======
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
# """
# interview/speech_to_text.py
# Transcribes user voice via OpenAI Whisper.
# Detects actual browser audio format (webm/wav/ogg) from magic bytes.
# """
# import os
# import io
# from openai import OpenAI, OpenAIError
# from dotenv import load_dotenv

# load_dotenv()


# def _get_client() -> OpenAI:
#     try:
#         import streamlit as st
#         key = st.secrets.get("OPENAI_API_KEY")
#     except Exception:
#         key = None
#     if not key:
#         key = os.getenv("OPENAI_API_KEY")
#     return OpenAI(api_key=key)


# def _detect_format(raw: bytes) -> str:
#     """Detect audio format from magic bytes — browsers record webm, not wav."""
#     if raw[:4] == b'RIFF':              return "wav"
#     if raw[:4] == b'fLaC':             return "flac"
#     if raw[:3] in (b'ID3', b'\xff\xfb'): return "mp3"
#     if raw[4:8] == b'ftyp':            return "mp4"
#     if raw[:4] == b'\x1a\x45\xdf\xa3': return "webm"   # Chrome / Firefox
#     if raw[:4] == b'OggS':             return "ogg"
#     return "webm"   # safe default for all modern browsers


# def transcribe_audio(audio_input) -> str:
#     """Returns transcribed text or empty string."""
#     text, _ = transcribe_audio_debug(audio_input)
#     return text


# def transcribe_audio_debug(audio_input) -> tuple[str, str]:
#     """
#     Returns (transcribed_text, debug_message).
#     debug_message is "ok" on success, error description on failure.
#     """
#     try:
#         # ── Read raw bytes ──────────────────────────────────
#         if hasattr(audio_input, "getvalue"):
#             raw = audio_input.getvalue()
#         elif hasattr(audio_input, "read"):
#             try:
#                 audio_input.seek(0)
#             except Exception:
#                 pass
>>>>>>> 4d0e189f (first update)
#             raw = audio_input.read()
#         else:
#             raw = bytes(audio_input)

<<<<<<< HEAD
#         if not raw or len(raw) < 500:
#             print(f"[Whisper] Audio too short: {len(raw) if raw else 0} bytes — nothing recorded?")
#             return ""

#         # Step 2 — detect actual format so Whisper knows what it's getting
#         fmt = _detect_format(raw)
#         print(f"[Whisper] Detected format: .{fmt}, size: {len(raw)} bytes")

#         # Step 3 — wrap in BytesIO with correct extension
#         buf = io.BytesIO(raw)
#         buf.name = f"recording.{fmt}"  # ← THIS is what was broken before

#         # Step 4 — send to Whisper
=======
#         if not raw:
#             return "", "No audio data received — mic may not have recorded"

#         size = len(raw)
#         if size < 500:
#             return "", f"Audio too short ({size} bytes) — try speaking longer"

#         # ── Detect format ────────────────────────────────────
#         fmt = _detect_format(raw)

#         # ── Build buffer with correct extension ──────────────
#         buf = io.BytesIO(raw)
#         buf.name = f"recording.{fmt}"

#         # ── Whisper API call ─────────────────────────────────
>>>>>>> 4d0e189f (first update)
#         client = _get_client()
#         result = client.audio.transcriptions.create(
#             model    = "whisper-1",
#             file     = buf,
#             language = "en"
#         )

<<<<<<< HEAD
#         text = result.text.strip() if result.text else ""
#         print(f"[Whisper] Transcribed: '{text[:120]}'")
#         return text

#     except OpenAIError as e:
#         print(f"[Whisper] OpenAI API error: {e}")
#         return ""
#     except Exception as e:
#         print(f"[Whisper] Unexpected error: {type(e).__name__}: {e}")
#         return ""
=======
#         text = (result.text or "").strip()
#         if not text:
#             return "", "Whisper returned empty — no speech detected in recording"

#         return text, "ok"

#     except OpenAIError as e:
#         return "", f"OpenAI error: {e}"
#     except Exception as e:
#         return "", f"{type(e).__name__}: {e}"

# # """
# # interview/speech_to_text.py
# # Transcribes user voice via OpenAI Whisper.

# # Root cause of "Could not transcribe" bug:
# #   - Browsers (Chrome/Firefox) record audio as .webm (not .wav)
# #   - We were naming the buffer "recording.wav" → Whisper rejected it
# #   - Fix: detect actual format from file header bytes, use correct extension
# # """
>>>>>>> 4d0e189f (first update)
# # import os
# # import io
# # from openai import OpenAI, OpenAIError
# # from dotenv import load_dotenv

# # load_dotenv()

<<<<<<< HEAD
# # def _get_client():
=======

# # def _get_client() -> OpenAI:
>>>>>>> 4d0e189f (first update)
# #     try:
# #         import streamlit as st
# #         key = st.secrets.get("OPENAI_API_KEY")
# #     except Exception:
# #         key = None
# #     if not key:
# #         key = os.getenv("OPENAI_API_KEY")
# #     return OpenAI(api_key=key)


<<<<<<< HEAD
# # def transcribe_audio(audio_input) -> str:
# #     """
# #     Transcribe voice using OpenAI Whisper.
# #     audio_input: file-like object from st.audio_input()
# #     Returns: transcribed string or ""
# #     """
# #     try:
# #         client = _get_client()

# #         # Read raw bytes from whatever st.audio_input() returns
# #         if hasattr(audio_input, "read"):
# #             raw = audio_input.read()
# #         elif hasattr(audio_input, "getvalue"):
# #             raw = audio_input.getvalue()
# #         else:
# #             raw = bytes(audio_input)

# #         if not raw or len(raw) < 100:
# #             print("[Whisper] Audio too short or empty")
# #             return ""

# #         # Wrap in BytesIO with a proper filename so Whisper accepts it
# #         audio_file = io.BytesIO(raw)
# #         audio_file.name = "answer.wav"

# #         transcript = client.audio.transcriptions.create(
# #             model    = "whisper-1",
# #             file     = audio_file,
# #             language = "en"
# #         )

# #         result = transcript.text.strip()
# #         print(f"[Whisper] Transcribed: {result[:80]}")
# #         return result

# #     except OpenAIError as e:
# #         print(f"[Whisper] OpenAI error: {e}")
# #         return ""
# #     except Exception as e:
# #         print(f"[Whisper] Unexpected error: {e}")
# #         return ""
# # # import os
=======
# # def _detect_format(raw: bytes) -> str:
# #     """
# #     Detect audio format from file header magic bytes.
# #     Returns the correct file extension for Whisper.
# #     """
# #     if raw[:4] == b'RIFF':
# #         return "wav"
# #     if raw[:4] == b'fLaC':
# #         return "flac"
# #     if raw[:3] == b'ID3' or raw[:2] == b'\xff\xfb':
# #         return "mp3"
# #     if raw[4:8] == b'ftyp':
# #         return "mp4"
# #     # WebM / Matroska — most browsers record this format
# #     if raw[:4] == b'\x1a\x45\xdf\xa3':
# #         return "webm"
# #     if raw[:3] == b'OggS':
# #         return "ogg"
# #     # Default fallback — webm is most common from browsers
# #     return "webm"


# # def transcribe_audio(audio_input) -> str:
# #     """
# #     Transcribe voice using Whisper.
# #     audio_input: UploadedFile from st.audio_input()
# #     Returns: transcribed text string, or "" on failure.
# #     """
# #     try:
# #         # Step 1 — read raw bytes from UploadedFile
# #         if hasattr(audio_input, "getvalue"):
# #             raw = audio_input.getvalue()
# #         elif hasattr(audio_input, "read"):
# #             audio_input.seek(0)
# #             raw = audio_input.read()
# #         else:
# #             raw = bytes(audio_input)

# #         if not raw or len(raw) < 500:
# #             print(f"[Whisper] Audio too short: {len(raw) if raw else 0} bytes — nothing recorded?")
# #             return ""

# #         # Step 2 — detect actual format so Whisper knows what it's getting
# #         fmt = _detect_format(raw)
# #         print(f"[Whisper] Detected format: .{fmt}, size: {len(raw)} bytes")

# #         # Step 3 — wrap in BytesIO with correct extension
# #         buf = io.BytesIO(raw)
# #         buf.name = f"recording.{fmt}"  # ← THIS is what was broken before

# #         # Step 4 — send to Whisper
# #         client = _get_client()
# #         result = client.audio.transcriptions.create(
# #             model    = "whisper-1",
# #             file     = buf,
# #             language = "en"
# #         )

# #         text = result.text.strip() if result.text else ""
# #         print(f"[Whisper] Transcribed: '{text[:120]}'")
# #         return text

# #     except OpenAIError as e:
# #         print(f"[Whisper] OpenAI API error: {e}")
# #         return ""
# #     except Exception as e:
# #         print(f"[Whisper] Unexpected error: {type(e).__name__}: {e}")
# #         return ""
# # # import os
# # # import io
>>>>>>> 4d0e189f (first update)
# # # from openai import OpenAI, OpenAIError
# # # from dotenv import load_dotenv

# # # load_dotenv()

<<<<<<< HEAD
# # # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
=======
# # # def _get_client():
# # #     try:
# # #         import streamlit as st
# # #         key = st.secrets.get("OPENAI_API_KEY")
# # #     except Exception:
# # #         key = None
# # #     if not key:
# # #         key = os.getenv("OPENAI_API_KEY")
# # #     return OpenAI(api_key=key)
>>>>>>> 4d0e189f (first update)


# # # def transcribe_audio(audio_input) -> str:
# # #     """
<<<<<<< HEAD
# # #     Transcribe voice answer using OpenAI Whisper.
# # #     Args:
# # #         audio_input: Output from st.audio_input() — a BytesIO object
# # #     Returns:
# # #         Transcribed text string, or "" on failure
# # #     """
# # #     try:
# # #         audio_input.name = "answer.wav"
# # #         transcript = client.audio.transcriptions.create(
# # #             model    = "whisper-1",
# # #             file     = audio_input,
# # #             language = "en"
# # #         )
# # #         return transcript.text.strip()
# # #     except OpenAIError as e:
# # #         print(f"[Whisper] Transcription error: {e}")
=======
# # #     Transcribe voice using OpenAI Whisper.
# # #     audio_input: file-like object from st.audio_input()
# # #     Returns: transcribed string or ""
# # #     """
# # #     try:
# # #         client = _get_client()

# # #         # Read raw bytes from whatever st.audio_input() returns
# # #         if hasattr(audio_input, "read"):
# # #             raw = audio_input.read()
# # #         elif hasattr(audio_input, "getvalue"):
# # #             raw = audio_input.getvalue()
# # #         else:
# # #             raw = bytes(audio_input)

# # #         if not raw or len(raw) < 100:
# # #             print("[Whisper] Audio too short or empty")
# # #             return ""

# # #         # Wrap in BytesIO with a proper filename so Whisper accepts it
# # #         audio_file = io.BytesIO(raw)
# # #         audio_file.name = "answer.wav"

# # #         transcript = client.audio.transcriptions.create(
# # #             model    = "whisper-1",
# # #             file     = audio_file,
# # #             language = "en"
# # #         )

# # #         result = transcript.text.strip()
# # #         print(f"[Whisper] Transcribed: {result[:80]}")
# # #         return result

# # #     except OpenAIError as e:
# # #         print(f"[Whisper] OpenAI error: {e}")
>>>>>>> 4d0e189f (first update)
# # #         return ""
# # #     except Exception as e:
# # #         print(f"[Whisper] Unexpected error: {e}")
# # #         return ""
<<<<<<< HEAD

# # # from deepgram import Deepgram
# # # import asyncio
# # # from config import DEEPGRAM_API_KEY

# # # dg = Deepgram(DEEPGRAM_API_KEY)

# # # async def transcribe(audio):

# # #     source = {'buffer': audio, 'mimetype': 'audio/wav'}

# # #     response = await dg.transcription.prerecorded(
# # #         source,
# # #         {'punctuate': True}
# # #     )

# # #     return response["results"]["channels"][0]["alternatives"][0]["transcript"]
=======
# # # # import os
# # # # from openai import OpenAI, OpenAIError
# # # # from dotenv import load_dotenv

# # # # load_dotenv()

# # # # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# # # # def transcribe_audio(audio_input) -> str:
# # # #     """
# # # #     Transcribe voice answer using OpenAI Whisper.
# # # #     Args:
# # # #         audio_input: Output from st.audio_input() — a BytesIO object
# # # #     Returns:
# # # #         Transcribed text string, or "" on failure
# # # #     """
# # # #     try:
# # # #         audio_input.name = "answer.wav"
# # # #         transcript = client.audio.transcriptions.create(
# # # #             model    = "whisper-1",
# # # #             file     = audio_input,
# # # #             language = "en"
# # # #         )
# # # #         return transcript.text.strip()
# # # #     except OpenAIError as e:
# # # #         print(f"[Whisper] Transcription error: {e}")
# # # #         return ""
# # # #     except Exception as e:
# # # #         print(f"[Whisper] Unexpected error: {e}")
# # # #         return ""

# # # # from deepgram import Deepgram
# # # # import asyncio
# # # # from config import DEEPGRAM_API_KEY

# # # # dg = Deepgram(DEEPGRAM_API_KEY)

# # # # async def transcribe(audio):

# # # #     source = {'buffer': audio, 'mimetype': 'audio/wav'}

# # # #     response = await dg.transcription.prerecorded(
# # # #         source,
# # # #         {'punctuate': True}
# # # #     )

# # # #     return response["results"]["channels"][0]["alternatives"][0]["transcript"]
>>>>>>> 4d0e189f (first update)
