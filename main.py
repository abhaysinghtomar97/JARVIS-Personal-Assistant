import os
import tempfile
import time
import webbrowser
import requests
import speech_recognition as sr
import pyttsx3
from gtts import gTTS
import pygame
from openai import OpenAI  # keep but use env var for key
import musicLibrary as musicLibrary

# Initialize once
pygame.mixer.init()
engine = pyttsx3.init()   # fallback TTS engine
recogniser = sr.Recognizer()

# --- TTS function using gTTS + pygame with tempfile ---
def speak(text, use_gtts=True):
    """Speak text. Try gTTS+pygame, fall back to pyttsx3 if gtts or pygame fails."""
    if not text:
        return

    if use_gtts:
        # create unique temp file
        tmpf = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp_path = tmpf.name
        tmpf.close()
        try:
            tts = gTTS(text)
            tts.save(tmp_path)

            # load & play
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()

            # wait until playback ends
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(30)

        except Exception as e:
            print("gTTS/pygame failed:", e)
            # fallback to pyttsx3
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception as e2:
                print("pyttsx3 also failed:", e2)
        finally:
            # make sure to stop playback before deleting file
            try:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
            except Exception:
                pass

            # small delay to ensure file handle released on Windows
            time.sleep(0.05)
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception as e:
                print("Could not remove temp file:", e)

    else:
        # direct pyttsx3 fallback
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print("pyttsx3 failed:", e)


# --- OpenAI helper (use env var for safety) ---
def aiprocess(command):
    api_key = os.getenv("OPENAI_API_KEY", "YOUR_KEY_HERE")
    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are Jarvis, a concise assistant. Keep responses short."},
            {"role": "user", "content": command}
        ],
        max_tokens=150
    )
    return completion.choices[0].message.content


# --- Command processing ---
def processCommand(c):
    c_lower = c.lower().strip()
    if "open google" in c_lower:
        webbrowser.open("https://google.com")

    elif "open facebook" in c_lower:
        webbrowser.open("https://facebook.com")

    elif "open instagram" in c_lower:
        webbrowser.open("https://instagram.com")

    elif "open youtube" in c_lower:
        webbrowser.open("https://youtube.com")

    elif "open github" in c_lower:
        webbrowser.open("https://github.com")

    elif c_lower.startswith("play "):
        # support multi-word song names
        song = c_lower.split(" ", 1)[1]
        link = musicLibrary.music.get(song)
        if link:
            webbrowser.open(link)
            speak(f"Playing {song}")
        else:
            speak("Song not found in library")

    elif c_lower.startswith("khabar"):
    # put your key here or set NEWSAPI_KEY in env (safer)
        api_key ="9f90c6300d7a4cb79ea3cfe96fbed950"

        if not api_key:
            speak("News API key not set.")
            return

        try:
            resp = requests.get(
                "https://newsapi.org/v2/top-headlines?country=us&apiKey=9f90c6300d7a4cb79ea3cfe96fbed950",
                params={"country": "us", "apiKey": api_key},
                timeout=6
            )
            resp.raise_for_status()
            data = resp.json()
            articles = data.get("articles", [])[:3]   # top 3 titles

            if not articles:
                speak("No news found.")
                return

            for art in articles:
                title = art.get("title")
                if title:
                    print("Headline:", title)
                    speak(title)

        except Exception as e:
            print("News error:", e)
            speak("Could not fetch news right now.")


    else:
        output = aiprocess(c)
        speak(output)


# --- Main listening loop with better error handling & ambient noise calibration ---
if __name__ == "__main__":
    speak("Initialising JARVIS. Ready.", use_gtts=True)

    # calibrate ambient noise once
    with sr.Microphone() as source:
        recogniser.adjust_for_ambient_noise(source, duration=1)
        print("Calibrated ambient noise")

    while True:
        try:
            with sr.Microphone() as source:
                print("Listening for wake word...")
                # increase timeout if needed; catches sr.WaitTimeoutError
                audio = recogniser.listen(source, timeout=5, phrase_time_limit=4)

            try:
                phrase = recogniser.recognize_google(audio)
                print("Heard:", phrase)
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                print("Speech API request error:", e)
                speak("Speech recognition service is unavailable", use_gtts=False)
                continue

            if "jarvis" in phrase.lower():
                speak("Yes sir", use_gtts=True)
                # listen for command after wake word
                with sr.Microphone() as source:
                    print("Listening for command...")
                    recogniser.adjust_for_ambient_noise(source, duration=0.5)
                    audio_cmd = recogniser.listen(source, timeout=6, phrase_time_limit=8)
                try:
                    command = recogniser.recognize_google(audio_cmd)
                    print("Command:", command)
                    processCommand(command)
                except sr.UnknownValueError:
                    speak("Sorry, I didn't catch that. Please try again.", use_gtts=False)
                except sr.RequestError as e:
                    print("RequestError:", e)
                    speak("Network problem with speech recognition", use_gtts=False)

        except sr.WaitTimeoutError:
            # no wake word detected before timeout - loop again
            continue
        except KeyboardInterrupt:
            print("Exiting...")
            break
        except Exception as e:
            print("Unexpected error:", e)
            # don't crash the loop; optionally speak minimal error
            # speak("An error occurred", use_gtts=False)
            continue
