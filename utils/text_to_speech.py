from gtts import gTTS
import uuid

def speak(text):

    filename = f"temp_{uuid.uuid4()}.mp3"

    tts = gTTS(text)
    tts.save(filename)

    return filename