import os
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def transcribe_audio(audio_input) -> str:
    """
    Transcribe voice answer using OpenAI Whisper.
    Args:
        audio_input: Output from st.audio_input() — a BytesIO object
    Returns:
        Transcribed text string, or "" on failure
    """
    try:
        audio_input.name = "answer.wav"
        transcript = client.audio.transcriptions.create(
            model    = "whisper-1",
            file     = audio_input,
            language = "en"
        )
        return transcript.text.strip()
    except OpenAIError as e:
        print(f"[Whisper] Transcription error: {e}")
        return ""
    except Exception as e:
        print(f"[Whisper] Unexpected error: {e}")
        return ""

# from deepgram import Deepgram
# import asyncio
# from config import DEEPGRAM_API_KEY

# dg = Deepgram(DEEPGRAM_API_KEY)

# async def transcribe(audio):

#     source = {'buffer': audio, 'mimetype': 'audio/wav'}

#     response = await dg.transcription.prerecorded(
#         source,
#         {'punctuate': True}
#     )

#     return response["results"]["channels"][0]["alternatives"][0]["transcript"]