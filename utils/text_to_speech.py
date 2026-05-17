"""
interview/text_to_speech.py
<<<<<<< HEAD
Browser Web Speech API via st.components.v1.html()
st.markdown() does NOT run JS — components.html() does.
height must be > 0 or Chrome blocks the iframe JS execution.
"""
import streamlit.components.v1 as components


def speak(text: str) -> None:
    if not text or not text.strip():
        return

    # Escape for safe JS string embedding
    safe = (
        text.strip()
        .replace("\\", "\\\\")
        .replace('"',  '\\"')
        .replace("'",  "\\'")
        .replace("\n", " ")
        .replace("\r", " ")
        .replace("`",  "\\`")
    )

    # height=1 (NOT 0) — Chrome silently blocks JS in 0-height iframes
    components.html(f"""
    <script>
    (function() {{
        try {{
            window.speechSynthesis.cancel();

            var msg = new SpeechSynthesisUtterance("{safe}");
            msg.lang   = 'en-US';
            msg.rate   = 0.92;
            msg.pitch  = 1.05;
            msg.volume = 1.0;

            function pickVoiceAndSpeak() {{
                var voices = window.speechSynthesis.getVoices();
                if (voices.length === 0) {{
                    setTimeout(pickVoiceAndSpeak, 150);
                    return;
                }}
                var order = [
                    'Google US English',
                    'Microsoft Zira - English (United States)',
                    'Samantha',
                    'Alex',
                ];
                var chosen = null;
                for (var i = 0; i < order.length; i++) {{
                    chosen = voices.find(function(v) {{
                        return v.name === order[i];
                    }});
                    if (chosen) break;
                }}
                if (!chosen) {{
                    chosen = voices.find(function(v) {{
                        return v.lang === 'en-US';
                    }});
                }}
                if (!chosen) {{
                    chosen = voices.find(function(v) {{
                        return v.lang.startsWith('en');
                    }});
                }}
                if (chosen) msg.voice = chosen;
                window.speechSynthesis.speak(msg);
            }}

            if (window.speechSynthesis.getVoices().length === 0) {{
                window.speechSynthesis.onvoiceschanged = pickVoiceAndSpeak;
            }} else {{
                pickVoiceAndSpeak();
            }}

        }} catch(e) {{
            console.warn('[LISA TTS]', e);
        }}
    }})();
    </script>
    """, height=1, scrolling=False)
# """
# text_to_speech.py
# Uses browser Web Speech API — no files created, no disk usage.
# LISA's voice plays directly in the browser via JavaScript.
# """
# import streamlit as st


# def speak(text: str) -> None:
#     """
#     Play text as speech using browser's built-in Web Speech API.
#     No MP3 files. No gTTS calls. No disk writes. Works everywhere.
#     """
#     if not text or not text.strip():
#         return

#     # Escape quotes so JS string doesn't break
#     safe = (
#         text.strip()
#         .replace("\\", "\\\\")
#         .replace('"', '\\"')
#         .replace("'", "\\'")
#         .replace("\n", " ")
#         .replace("\r", " ")
#     )

#     st.markdown(f"""
=======
Sarvam AI TTS — bulbul:v3
Replaces browser Web Speech API with Sarvam's Indian-language voice.
Plays audio inline via HTML5 <audio autoplay>.
"""
import os
import base64
import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

SARVAM_KEY = os.getenv("SARVAM_AI") or os.getenv("SARVAM_API_KEY", "")
TTS_URL    = "https://api.sarvam.ai/text-to-speech"

# ── Default voice settings (can override per call) ───────────────────────────
DEFAULT_SPEAKER  = "ratan"  # male voice requested by user
DEFAULT_LANGUAGE = "en-IN"    # switch to "hi-IN" for Hindi
DEFAULT_PACE     = 0.95


def speak(
    text: str,
    language: str = DEFAULT_LANGUAGE,
    speaker: str  = DEFAULT_SPEAKER,
    pace: float   = DEFAULT_PACE,
) -> None:
    """
    Convert text to speech using Sarvam bulbul:v3.
    Plays audio automatically in the browser.
    Falls back to browser Web Speech API if Sarvam key is missing.
    """
    if not text or not text.strip():
        return

    if not SARVAM_KEY:
        # Graceful fallback — browser TTS (same as old behaviour)
        _browser_speak(text)
        return

    audio_bytes = _sarvam_tts(text.strip(), language, speaker, pace)
    if audio_bytes:
        _play_audio(audio_bytes)
    else:
        # Fallback if API call fails
        _browser_speak(text)


# ════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ════════════════════════════════════════════════════════════════

def _sarvam_tts(text: str, language: str, speaker: str, pace: float) -> bytes | None:
    """
    Call Sarvam /text-to-speech.
    Returns raw WAV bytes or None on failure.
    Max 2500 chars per request — longer text is split automatically.
    """
    # Split long text into chunks of 2400 chars on sentence boundaries
    chunks = _split_text(text, max_len=2400)
    all_audio = b""

    for chunk in chunks:
        payload = {
            "inputs":               [chunk],
            "target_language_code": language,
            "speaker":              speaker,
            "model":                "bulbul:v3",
            "enable_preprocessing": True,   # handles Hinglish / mixed script
            "pace":                 pace,
        }
        try:
            resp = requests.post(
                TTS_URL,
                headers={"api-subscription-key": SARVAM_KEY},
                json=payload,
                timeout=20,
            )
            resp.raise_for_status()
            audios = resp.json().get("audios", [])
            if audios:
                all_audio += base64.b64decode(audios[0])
        except requests.exceptions.HTTPError as e:
            st.warning(f"[Sarvam TTS] HTTP {e.response.status_code}: {e.response.text[:200]}")
            return None
        except Exception as e:
            st.warning(f"[Sarvam TTS] Error: {e}")
            return None

    return all_audio if all_audio else None


def _split_text(text: str, max_len: int = 2400) -> list[str]:
    """Split text into chunks ≤ max_len chars, breaking on sentence ends."""
    if len(text) <= max_len:
        return [text]

    chunks, current = [], ""
    for sentence in text.replace("। ", ".\n").split(". "):
        sentence = sentence.strip()
        if not sentence:
            continue
        candidate = current + (". " if current else "") + sentence
        if len(candidate) <= max_len:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)
    return chunks or [text[:max_len]]


def _play_audio(audio_bytes: bytes) -> None:
    """Inject an autoplay HTML5 audio player into the Streamlit page."""
    b64 = base64.b64encode(audio_bytes).decode()
    components.html(
        f"""
        <audio autoplay style="display:none;">
            <source src="data:audio/wav;base64,{b64}" type="audio/wav">
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
# """
# interview/text_to_speech.py
# Browser Web Speech API via st.components.v1.html()
# st.markdown() does NOT run JS — components.html() does.
# height must be > 0 or Chrome blocks the iframe JS execution.
# """
# import streamlit.components.v1 as components


# def speak(text: str) -> None:
#     if not text or not text.strip():
#         return

#     # Escape for safe JS string embedding
#     safe = (
#         text.strip()
#         .replace("\\", "\\\\")
#         .replace('"',  '\\"')
#         .replace("'",  "\\'")
#         .replace("\n", " ")
#         .replace("\r", " ")
#         .replace("`",  "\\`")
#     )

#     # height=1 (NOT 0) — Chrome silently blocks JS in 0-height iframes
#     components.html(f"""
>>>>>>> 4d0e189f (first update)
#     <script>
#     (function() {{
#         try {{
#             window.speechSynthesis.cancel();
<<<<<<< HEAD
#             var u = new SpeechSynthesisUtterance("{safe}");
#             u.rate  = 0.95;
#             u.pitch = 1.0;
#             u.volume = 1.0;
#             // Pick a natural English voice if available
#             var voices = window.speechSynthesis.getVoices();
#             var preferred = voices.find(function(v) {{
#                 return v.lang === 'en-US' && v.localService === true;
#             }});
#             if (!preferred) {{
#                 preferred = voices.find(function(v) {{
#                     return v.lang.startsWith('en');
#                 }});
#             }}
#             if (preferred) u.voice = preferred;
#             window.speechSynthesis.speak(u);
#         }} catch(e) {{
#             console.warn('TTS error:', e);
#         }}
#     }})();
#     </script>
#     """, unsafe_allow_html=True)
# # from gtts import gTTS
# # import uuid

# # def speak(text):

# #     filename = f"temp_{uuid.uuid4()}.mp3"

# #     tts = gTTS(text)
# #     tts.save(filename)

# #     return filename
=======

#             var msg = new SpeechSynthesisUtterance("{safe}");
#             msg.lang   = 'en-US';
#             msg.rate   = 0.92;
#             msg.pitch  = 1.05;
#             msg.volume = 1.0;

#             function pickVoiceAndSpeak() {{
#                 var voices = window.speechSynthesis.getVoices();
#                 if (voices.length === 0) {{
#                     setTimeout(pickVoiceAndSpeak, 150);
#                     return;
#                 }}
#                 var order = [
#                     'Google US English',
#                     'Microsoft Zira - English (United States)',
#                     'Samantha',
#                     'Alex',
#                 ];
#                 var chosen = null;
#                 for (var i = 0; i < order.length; i++) {{
#                     chosen = voices.find(function(v) {{
#                         return v.name === order[i];
#                     }});
#                     if (chosen) break;
#                 }}
#                 if (!chosen) {{
#                     chosen = voices.find(function(v) {{
#                         return v.lang === 'en-US';
#                     }});
#                 }}
#                 if (!chosen) {{
#                     chosen = voices.find(function(v) {{
#                         return v.lang.startsWith('en');
#                     }});
#                 }}
#                 if (chosen) msg.voice = chosen;
#                 window.speechSynthesis.speak(msg);
#             }}

#             if (window.speechSynthesis.getVoices().length === 0) {{
#                 window.speechSynthesis.onvoiceschanged = pickVoiceAndSpeak;
#             }} else {{
#                 pickVoiceAndSpeak();
#             }}

#         }} catch(e) {{
#             console.warn('[LISA TTS]', e);
#         }}
#     }})();
#     </script>
#     """, height=1, scrolling=False)
# # """
# # text_to_speech.py
# # Uses browser Web Speech API — no files created, no disk usage.
# # LISA's voice plays directly in the browser via JavaScript.
# # """
# # import streamlit as st


# # def speak(text: str) -> None:
# #     """
# #     Play text as speech using browser's built-in Web Speech API.
# #     No MP3 files. No gTTS calls. No disk writes. Works everywhere.
# #     """
# #     if not text or not text.strip():
# #         return

# #     # Escape quotes so JS string doesn't break
# #     safe = (
# #         text.strip()
# #         .replace("\\", "\\\\")
# #         .replace('"', '\\"')
# #         .replace("'", "\\'")
# #         .replace("\n", " ")
# #         .replace("\r", " ")
# #     )

# #     st.markdown(f"""
# #     <script>
# #     (function() {{
# #         try {{
# #             window.speechSynthesis.cancel();
# #             var u = new SpeechSynthesisUtterance("{safe}");
# #             u.rate  = 0.95;
# #             u.pitch = 1.0;
# #             u.volume = 1.0;
# #             // Pick a natural English voice if available
# #             var voices = window.speechSynthesis.getVoices();
# #             var preferred = voices.find(function(v) {{
# #                 return v.lang === 'en-US' && v.localService === true;
# #             }});
# #             if (!preferred) {{
# #                 preferred = voices.find(function(v) {{
# #                     return v.lang.startsWith('en');
# #                 }});
# #             }}
# #             if (preferred) u.voice = preferred;
# #             window.speechSynthesis.speak(u);
# #         }} catch(e) {{
# #             console.warn('TTS error:', e);
# #         }}
# #     }})();
# #     </script>
# #     """, unsafe_allow_html=True)
# # # from gtts import gTTS
# # # import uuid

# # # def speak(text):

# # #     filename = f"temp_{uuid.uuid4()}.mp3"

# # #     tts = gTTS(text)
# # #     tts.save(filename)

# # #     return filename
>>>>>>> 4d0e189f (first update)
