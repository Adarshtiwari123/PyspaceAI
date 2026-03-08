import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def speak_question(text):

    speech = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text
    )

    file_path = "temp_question.mp3"

    with open(file_path, "wb") as f:
        f.write(speech.content)

    return file_path