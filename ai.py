import core_controls.assist as assist
import tools
import whisper
import speech_recognition as sr
import io
import torch
import time
import modules.cse as cse
import os
from datetime import datetime, timedelta
from queue import Queue
from tempfile import NamedTemporaryFile
from RealtimeSTT import AudioToTextRecorder


# Initialize necessary variables and models
is_waiting_for_response = False


def main():
    global is_waiting_for_response
    phrase_time = None
    tts_enabled = True

    last_sample = bytes()
    #record_timeout = 5
    #phrase_timeout = 8
    temp_file = NamedTemporaryFile().name
    transcription = ['']
    triggers = ["hi jarvis"]

    data_queue = Queue()

    audio_model = whisper.load_model("tiny.en")

    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    mic = sr.Microphone(sample_rate=16000, device_index=1)

    def mute_microphone(recognizer):
        recognizer.energy_threshold = 3000

    def unmute_microphone(recognizer):
        recognizer.energy_threshold = 1000

    def record_callback(_, audio: sr.AudioData) -> None:
        data = audio.get_raw_data()
        data_queue.put(data)

    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=2)
    print("Microphone set and adjusted for ambient noise.")

    def handle_search_request(query):
        search_results = cse.google_search(query, os.environ.get("GOOGLE_API_KEY"), os.environ.get("GOOGLE_CSE_ID"))
        results_string = "\n".join([f"From: {result['title']} on {result['displayLink']}\n Snippet: {result['snippet']}\n" for result in search_results[:3]])
        return results_string

    recognizer.listen_in_background(source, record_callback,
                                    phrase_time_limit=2)

    print("Jarvis initialized and listening. Main loop started.")

    while True:
        now = datetime.now()
        if not data_queue.empty():
            phrase_complete = False
            if (phrase_time and now - phrase_time >
                    timedelta(seconds=2)):
                last_sample = bytes()
                phrase_complete = True
            phrase_time = now

            while not data_queue.empty():
                data = data_queue.get()
                last_sample += data

            audio_data = sr.AudioData(last_sample, source.SAMPLE_RATE,
                                      source.SAMPLE_WIDTH)
            wav_data = io.BytesIO(audio_data.get_wav_data())

            with open(temp_file, 'w+b') as f:
                f.write(wav_data.read())

            result = audio_model.transcribe(temp_file,
                                            fp16=torch.cuda.is_available())
            text = result['text'].strip()

            if phrase_complete:
                transcription.append(text)

                if is_waiting_for_response:
                    if text:
                        unmute_microphone(recognizer)
                        print("Listening for users response...")
                        print("User: " + text)
                        response = assist.ask_question_memory(text)
                        print("Jarvis: " + response)
                        speech = response.split("#")[0]

                        # Check for commands
                        if len(response.split("#")) > 1:
                            command = response.split("#")[1]
                            tools.parse_command(command)
                        if tts_enabled:
                            mute_microphone(recognizer)
                            done = assist.TTS(speech)
                            print(done)

                        is_waiting_for_response = False
                else:
                    if any(trigger in text.lower() for trigger in triggers):
                        if text:
                            unmute_microphone(recognizer)
                            print("Listening for triggers...")
                            print("User: " + text)

                            # Check if the text contains a search command
                            trigger_phrase = "search for"
                            if trigger_phrase in text.lower():
                                query = text.lower().split(
                                    trigger_phrase, 1)[1].strip()
                                response = handle_search_request(query)
                                response = "Here are the top three search results I found:\n" + response
                                print("Jarvis: " + response)
                                speech = response
                            else:
                                response = assist.ask_question_memory(text)
                                print("Jarvis: " + response)
                                speech = response.split("#")[0]

                                # Check for commands
                                if len(response.split("#")) > 1:
                                    command = response.split("#")[1]
                                    tools.parse_command(command)

                            if tts_enabled:
                                mute_microphone(recognizer)
                                done = assist.TTS(speech)
                                print(done)

                            # Set the state to waiting for response
                            is_waiting_for_response = True
                    else:
                        print("Listening...")
            else:
                transcription[-1] = text
            print('', end='', flush=True)

            # Sleep to preserve processor.
            time.sleep(0.25)


if __name__ == "__main__":
    main()
