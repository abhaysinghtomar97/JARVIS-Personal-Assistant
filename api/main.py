import speech_recognition as sr  
import webbrowser
import pyttsx3 
import api.musicLibrary as musicLibrary
import requests
from openai import OpenAI
from gtts import gTTS
import pygame
import os
from http.server import BaseHTTPRequestHandler #for vercel deploy.

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Hello from my Python app on Vercel!")

# pip install pocketsphinx

recogniser = sr.Recognizer()
engine  = pyttsx3.init()
newsapi ="9f90c6300d7a4cb79ea3cfe96fbed950"

# Initialize pygame mixer ONCE at the start
pygame.mixer.init()

# Old pyttsx3 speak function
def speak_old(text):
    engine.say(text)
    engine.runAndWait()

# New gTTS + pygame speak function
def speak(text):
    # Save temp file to current working directory
    temp_path = os.path.join(os.getcwd(), "temp.mp3")
    tts = gTTS(text)
    tts.save(temp_path)

    try:
        # Load the MP3 file
        pygame.mixer.music.load(temp_path) 
        # Play the music
        pygame.mixer.music.play()
        # Keep the program running until music finishes
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except pygame.error as e:
        print(f"Pygame error: {e}")
    finally:
       pygame.mixer.music.stop()     # stop playback
       pygame.mixer.quit()           # release the file handle
       pygame.mixer.init()           # reinit for next play
       if os.path.exists(temp_path):
           os.remove(temp_path)

def aiprocess(command):
    client = OpenAI(
        api_key="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"
    )
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a virtual assistant named Jarvis assistant, skilled in general task like Alexa and Google Cloud. Give short responses"},
            {"role": "user", "content": command}
        ]
    )
    return completion.choices[0].message.content

def processCommand(c):
    if "open google" in c.lower():
        webbrowser.open("https://google.com")
    
    elif "open facebook" in c.lower():
        webbrowser.open("https://facebook.com")
    
    elif "open instagram" in c.lower():
        webbrowser.open("https://instagram.com")
    
    elif "open youtube" in c.lower():
        webbrowser.open("https://youtube.com")
    
    elif "open github" in c.lower():
        webbrowser.open("https://github.com")

    elif c.lower().startswith("play"):
        song = c.lower().split(" ")[1]
        link = musicLibrary.music[song]
        webbrowser.open(link)

    elif c.lower().startswith("khabar"):
        r = requests.get("https://newsapi.org/v2/top-headlines?country=us&apiKey=9f90c6300d7a4cb79ea3cfe96fbed950")
        if r.status_code == 200:
            # Parse the JSON response
            data = r.json()

            # Extract the headlines
            articles = data.get('articles', [])

            # Speaking headlines
            for article in articles:
                speak(article['title'])

    else:
        # Let OpenAI handle the request
        output = aiprocess(c)
        speak(output)

if __name__ == "__main__":
    speak("Initialising JARVIS.....")
    while True:
        # Obtain audio from the microphone
        r = sr.Recognizer()

        try:
            with sr.Microphone() as source:
                print("Listening...")
                audio = r.listen(source, timeout=2)

            word = r.recognize_google(audio)

            if "jarvis" in word.lower():
                speak("Yes Sir")
                # Listen for command
                with sr.Microphone() as source:
                    print("Jarvis Active...")
                    audio = r.listen(source)
                    command = r.recognize_google(audio)
                    processCommand(command)

        except Exception as e:
            print("Error; {0}".format(e))
