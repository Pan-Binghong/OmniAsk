import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key = os.getenv("OPENAI_API_KEY"),
    base_url = os.getenv("OPENAI_BASE_URL")
)

model_name = "whisper-1"

transcript = client.audio.transcriptions.create(
    model=model_name,
    file=open("speech2text/test.mp3", "rb"),
    response_format="verbose_json"
)

print(transcript)
