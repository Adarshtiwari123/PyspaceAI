import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def transcribe_audio(audio_file):

    with open(audio_file, "rb") as file:

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=file
        )

    return transcript.text