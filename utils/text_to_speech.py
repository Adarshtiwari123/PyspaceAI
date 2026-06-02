"""
Deepgram TTS — Aura-2
Replaces browser Web Speech API with Deepgram's Ophelia voice.
Plays audio inline via HTML5 <audio autoplay>.
"""
import os
import base64
import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

TTS_URL = "https://api.deepgram.com/v1/speak?model=aura-2-ophelia-en"

# We use the defaults from the original implementation but ignore them for Deepgram
DEFAULT_SPEAKER  = "aura-2-ophelia-en"  
DEFAULT_LANGUAGE = "en-IN"    
DEFAULT_PACE     = 1.0


def speak(
    text: str,
    language: str = DEFAULT_LANGUAGE,
    speaker: str  = DEFAULT_SPEAKER,
    pace: float   = DEFAULT_PACE,
) -> None:
    """
    Convert text to speech using Deepgram Aura-2.
    Plays audio automatically in the browser.
    Falls back to browser Web Speech API if Deepgram key is missing or fails.
    """
    if not text or not text.strip():
        return

    load_dotenv(override=True)
    api_key = os.getenv("DEEPGRAM_API_KEY", "").strip()

    if not api_key:
        # Graceful fallback — browser TTS (same as old behaviour)
        _browser_speak(text)
        return

    audio_bytes = _deepgram_tts(text.strip(), api_key)
    if audio_bytes:
        _play_audio(audio_bytes)
    else:
        # Fallback if API call fails
        _browser_speak(text)


# ════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ════════════════════════════════════════════════════════════════

def _deepgram_tts(text: str, api_key: str) -> bytes | None:
    """
    Call Deepgram /speak API.
    Returns raw MP3 bytes or None on failure.
    """
    payload = {
        "text": text
    }
    try:
        resp = requests.post(
            TTS_URL,
            headers={
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=20,
        )
        resp.raise_for_status()
        return resp.content
    except requests.exceptions.HTTPError as e:
        st.warning(f"[Deepgram TTS] HTTP {e.response.status_code}: {e.response.text[:200]}")
        return None
    except Exception as e:
        st.warning(f"[Deepgram TTS] Error: {e}")
        return None


def _play_audio(audio_bytes: bytes) -> None:
    """Inject an autoplay HTML5 audio player into the Streamlit page."""
    b64 = base64.b64encode(audio_bytes).decode()
    components.html(
        f"""
        <audio autoplay style="display:none;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mpeg">
        </audio>
        """,
        height=1,
        scrolling=False,
    )


def _browser_speak(text: str) -> None:
    """Fallback: browser Web Speech API (original behaviour)."""
    safe = (
        text.strip()
        .replace("\\", "\\\\")
        .replace('"',  '\\"')
        .replace("'",  "\\'")
        .replace("\n", " ")
        .replace("\r", " ")
        .replace("`",  "\\`")
    )
    components.html(
        f"""
        <script>
        (function() {{
            try {{
                window.speechSynthesis.cancel();
                var msg = new SpeechSynthesisUtterance("{safe}");
                msg.lang = 'en-IN';
                msg.rate = 0.92;
                msg.pitch = 1.05;
                msg.volume = 1.0;
                function pickAndSpeak() {{
                    var voices = window.speechSynthesis.getVoices();
                    if (!voices.length) {{ setTimeout(pickAndSpeak, 150); return; }}
                    var v = voices.find(v => v.lang === 'en-IN')
                         || voices.find(v => v.lang === 'en-US')
                         || voices.find(v => v.lang.startsWith('en'));
                    if (v) msg.voice = v;
                    window.speechSynthesis.speak(msg);
                }}
                if (!window.speechSynthesis.getVoices().length)
                    window.speechSynthesis.onvoiceschanged = pickAndSpeak;
                else pickAndSpeak();
            }} catch(e) {{ console.warn('[LISA TTS fallback]', e); }}
        }})();
        </script>
        """,
        height=1,
        scrolling=False,
    )
