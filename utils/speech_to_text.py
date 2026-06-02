"""
Deepgram STT — Nova-3
Replaces Sarvam with Deepgram's speech recognition.
Supports English (Indian accent).
Keeps the same function signatures as the old version so nothing
else in your codebase needs to change.
"""
import os
import requests
from dotenv import load_dotenv

import streamlit as st

STT_URL = "https://api.deepgram.com/v1/listen?model=nova-3&language=en-IN"

DEFAULT_LANGUAGE = "en-IN"


def transcribe_audio(audio_input, language: str = DEFAULT_LANGUAGE) -> str:
    """
    Transcribe voice using Deepgram Nova-3.
    """
    text, debug = transcribe_audio_debug(audio_input, language)
    if not text and debug != "ok":
        st.error(f"STT Error: {debug}")
    return text


def transcribe_audio_debug(
    audio_input,
    language: str = DEFAULT_LANGUAGE,
) -> tuple[str, str]:
    load_dotenv(override=True)
    api_key = os.getenv("DEEPGRAM_API_KEY", "").strip()

    if not api_key:
        return "", "DEEPGRAM_API_KEY key not set in .env"

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
            if isinstance(audio_input, str):
                raw = audio_input.encode("utf-8")
            else:
                raw = bytes(audio_input)
    except Exception as e:
        return "", f"Failed to read audio bytes: {e}"

    if not raw:
        return "", "No audio data received — mic may not have recorded"
    if len(raw) < 500:
        return "", f"Audio too short ({len(raw)} bytes) — try speaking longer"

    try:
        # Deepgram expects raw binary audio in the body, with a generic content-type
        # You can specify exact mime if needed, but audio/webm is common for browser uploads.
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "audio/webm" 
        }
        
        # Override language if passed
        url = STT_URL
        if language and language != "unknown":
            url = f"https://api.deepgram.com/v1/listen?model=nova-3&language={language}"

        resp = requests.post(url, headers=headers, data=raw, timeout=30)
        resp.raise_for_status()

        data = resp.json()
        transcript = data.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get("transcript", "").strip()

        if not transcript:
            return "", "Deepgram returned empty transcript — no speech detected"

        print(f"[Deepgram STT] Transcribed ({len(raw)}B): '{transcript[:120]}'")
        return transcript, "ok"

    except requests.exceptions.HTTPError as e:
        detail = e.response.text[:300] if e.response else str(e)
        return "", f"Deepgram STT HTTP {e.response.status_code}: {detail}"
    except Exception as e:
        return "", f"{type(e).__name__}: {e}"
