"""
interview/text_to_speech.py
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
#     <script>
#     (function() {{
#         try {{
#             window.speechSynthesis.cancel();
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