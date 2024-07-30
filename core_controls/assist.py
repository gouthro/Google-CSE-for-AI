from openai import OpenAI
from datetime import datetime
from pygame import mixer
import time
import os
import openlit

# Initialize OpenLit
openlit.init(otlp_endpoint="http://127.0.0.1:4318", collect_gpu_stats=True)

client = OpenAI(default_headers={"OpenAI-Beta": "assistant=v2"}, api_key=os.environ.get("OPENAI_API_KEY"),)
mixer.init()

assistant_id = os.environ.get("OPENAI_ASSISTANT_ID")
thread_id = os.environ.get("OPENAI_THREAD_ID")

assistant = client.beta.assistants.retrieve(assistant_id)
thread = client.beta.threads.retrieve(thread_id)


def ask_question_memory(question):
    global thread

    client.beta.threads.messages.create(
        thread.id,
        role="user",
        content=question,
        )
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )
    while (
        run_status := client.beta.threads.runs.retrieve(
          thread_id=thread.id,
          run_id=run.id
        )
    ).status != 'completed':
        if run_status.status == 'failed':
            return "The run failed."
        time.sleep(1)
    # Retrieve messages after the run has succeeded
    messages = client.beta.threads.messages.list(
      thread_id=thread.id
    )
    return messages.data[0].content[0].text.value


# Function to generate TTS and return the path
def generate_tts(sentence, speech_file_path):
    response = client.audio.speech.create(
        model="tts-1",
        voice="echo",
        input=sentence,
    )
    response.stream_to_file(speech_file_path)
    return str(speech_file_path)


# Function to play the audio file
def play_sound(file_path):
    mixer.music.load(file_path)
    mixer.music.play()


# Function to play the TTS for each sentence
def TTS(text):
    # speech_file_path = "speech.mp3"
    speech_file_path = generate_tts(text, "speech.mp3")
    play_sound(speech_file_path)
    while mixer.music.get_busy():
        time.sleep(1)
    mixer.music.unload()
    os.remove(speech_file_path)

    return "done"
