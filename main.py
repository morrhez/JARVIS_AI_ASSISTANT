import speech_recognition as sr
import webbrowser # helps to open websites
# import pyttsx3
import music_library
from openai import OpenAI
import subprocess
import traceback #helps to trace where error is occuring
import random #helps to generate random output from any given parameters
import pygame #for interface design
from jarvis_interface import Jarvis_interface
import threading #runs the assistant in the background while the interface window uses the main thread
import re  #helps to pull the number of minutes out of the command
import os
import study_library
import json
from datetime import datetime  # for time and date
import wikipedia  # pip install wikipedia
import pyjokes
# import os (for removing the MP3 file)
# from gtts import gTTS (A better tts option but need google cloud subscription after few uses)

# pip install pocketsphinx

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")   #if leave empty then OpenAI integrated feature is off
wikipedia.wikipedia.USER_AGENT = "JarvisAssistant/1.0 (student project)"
interface = Jarvis_interface()
recognizer = sr.Recognizer()
# engine = pyttsx3.init() #deleted, speak() creates its own everytime

# def speak(text):
#     print("Speaking:", text)
#     engine = pyttsx3.init()
#     engine.say(text)
#     engine.runAndWait()
#     engine.stop()


def speak(text):
    print("Speaking:", text)
    interface.set_state("speaking")   # HUD: turn to speaking colour
    interface.log(text)               # HUD: show what Jarvis says
    safe = text.replace("'", "''").replace("\n", " ")
    subprocess.run([
        "powershell", "-Command",
        f"Add-Type -AssemblyName System.Speech; "
        f"(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{safe}')"
    ])
    interface.set_state("idle")       # HUD: back to idle after speaking

def speak_quietly(text):
    # same as speak(), but without interface.log(), so nothing shows in the HUD
    safe = text.replace("'", "''").replace("\n", " ")
    subprocess.run([
        "powershell", "-Command",
        f"Add-Type -AssemblyName System.Speech; "
        f"(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{safe}')"
    ])

#CODE FOR PLAYING MP3 FILE BY PYGAME
# def speak(text):
#     tts = gTTS(text)
#     tts.save('temp.mp3')

#     #Initialize Pygame mixer
    # pygame.mixer.init()

#     #Load the MP3 file
#     pygame.mixer.music.get_busy('temp.mp3')

#     #Play the MP3 file
#     pygame.mixer.music.play()

#     #keep the program working until the music stops playing
#     while pygame.mixer.music.load.get_busy():
#         pygame.time.Clock().tick(10)

#     os.remove("temp.mp3")
#     os.remove

# ACCESING CHATGPT 
def ai_process(command):
    user = OpenAI(api_key=OPENAI_API_KEY)

    completion = user.chat.completions.create(
        model="gpt-3.5-turbo", #can be changed by the user for their own preference
        messages=[
            {"role": "system", "content": "You are a virtual assistant named Jarvis, skilled in general tasks like Alexa and Google Cloud."},
            {"role": "user", "content": command}
        ]
    )

    return completion.choices[0].message.content

#STUDENT FRIENDLY STUDY MODE
#  motivational lines and study timer
study_quotes = [
    "Stay focused. Small steps every day lead to big results.",
    "Discipline beats motivation. Let's get started.",
    "One chapter at a time. You have got this.",
    "Future you will thank you for studying today.",
    "Do not stop when you are tired. Stop when you are done.",
]

timer_cancel = threading.Event()   # setting this to cancels a running timer

def study_timer(minutes):
    interface.log(f"Study timer started: {minutes} min")
    interface.start_countdown(minutes * 60)          #show a countdown on interface
    cancelled = timer_cancel.wait(minutes * 60)  # sleeps in the background; True if cancelled
    interface.stop_countdown()                       #remove countdown when done/cancelled
    if cancelled:
        interface.log("Study timer cancelled")
    else:
        speak(f"Time's up . Your {minutes} minute study session is complete.")
        speak(random.choice(study_quotes))

#JARVIS MEMORY: remembers things the user tells it
MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_memory.json")

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def clean_key(text):
    return text.lower().replace("favourite", "favorite").strip(" ?.!")

memory = load_memory()

#JOKES
#Jokes library (optional) otherwise random jokes from pyjoke module will be used
# jokes = [
#     "Why do programmers prefer dark mode? Because light attracts bugs.",
#     "Why did the student eat his homework? Because the teacher said it was a piece of cake.",
#     "I told my computer I needed a break, and it said no problem, I will go to sleep.",
#     "Why was the math book sad? It had too many problems.",
#     "There are ten types of people in the world. Those who understand binary and those who do not.",
#     "Why was the computer cold? It left its windows open.",
# ]

#COMMANDS AND RESPONSES 
def processCommand(c):
    interface.set_state("thinking")           # HUD: amber + fast rings while processing
    interface.log("Command: " + c)            # HUD: show the command you gave

    if "how r u" in c.lower():
        replies = [
            "I am doing great sir.",
            "Fully operational and at your service sir.",
        ]
        speak(random.choice(replies))

#JARVIS MEMORY
    elif (m := re.search(r"forget my (.+)", c, re.IGNORECASE)):
        key = clean_key(m.group(1))
        if key in memory:
            del memory[key]
            save_memory(memory)
            speak(f"Okay, I have forgotten your {key}.")
        else:
            speak(f"I do not have your {key} saved.")

    elif "reset" in c.lower() or "reset memory" in c.lower() or "forget" in c.lower() or "forget everything" in c.lower() or "reset history" in c.lower():
        memory.clear()
        save_memory(memory)
        speak("My memory has been reset sucessfully.")

    elif (m := re.search(r"forget my (.+)", c, re.IGNORECASE)):
        key = clean_key(m.group(1))
        if key in memory:
            del memory[key]
            save_memory(memory)
            speak(f"Okay, I have forgotten your {key}.")
        else:
            speak(f"I do not have your {key} saved.")

    elif (m := re.match(r"(?:remember (?:that )?)?my (name|favou?rite .+?) is (.+)", c.strip(), re.IGNORECASE)):
        key = clean_key(m.group(1))
        memory[key] = m.group(2).strip()
        save_memory(memory)
        speak(f"Got it . Your {key} is {memory[key]}.")

    elif (m := re.match(r"what(?:'s| is) my (.+)", c.strip(), re.IGNORECASE)):
        key = clean_key(m.group(1))
        if key in memory:
            speak(f"Your {key} is {memory[key]}.")
        else:
            speak(f"I do not know your {key} yet . You can tell me and I will save it")

#WIKIPEDIA
    elif (m := re.search(r"(?:tell me about|wikipedia)\s+(.+)", c, re.IGNORECASE)):
        topic = re.sub(r"^(for|about)\s+", "", m.group(1).strip(), flags=re.IGNORECASE)
        interface.log("Searching Wikipedia: " + topic)
        try:
            results = wikipedia.search(topic)
            if not results:
                speak(f"I could not find anything about {topic} on wikipedia sir.")
            else:
                summary = wikipedia.summary(results[0], sentences=2, auto_suggest=False)
                summary = re.sub(r"\(.*?\)", "", summary)   # removes brackets (pronunciations, dates) so speech sounds natural
                summary = summary.replace("‘", "'").replace("’", "'")   # curly quotes can break the PowerShell voice
                speak(summary)
        except wikipedia.exceptions.DisambiguationError as e:
            speak(f"{topic} can mean many things, like {e.options[0]} or {e.options[1]}. Please be more specific.")
        except Exception as e:
            print("Wikipedia error:", repr(e))
            traceback.print_exc()
            speak("I could not reach wikipedia sir. Please check your internet connection.")

#TIME AND DATE
    elif re.search(r"what time|(what'?s|what is|tell me) the time|current time", c.lower()):
        speak("It is " + datetime.now().strftime("%I:%M %p").lstrip("0"))

    elif re.search(r"what day|(what'?s|what is|tell me)( the| today'?s)? date", c.lower()):
        speak("Today is " + datetime.now().strftime("%A, %d %B %Y"))

#JOKES

#from jokes library(only if jokes library is in the program)
#    elif "joke" in c.lower():
#        speak(random.choice(jokes))

#from pyjoke module
    elif "joke" in c.lower():
        joke = pyjokes.get_joke()
        print(joke)
        speak(joke)

#SELF-INTRODUCTON AND BASIC DETAILS OF JARVIS
    elif "introduce yourself" in c.lower():
        speak("Hello everyone, my name is Jarvis. I am a AI assistant.")

    elif "what can you do" in c.lower():
       speak("I can answer your queries, open websites & folders, play music, set a timer, save your informations, tell the time and date, tell jokes, search wikipedia and other things too.")

    elif "can you do my homework" in c.lower():
        speak("I cannot write your assignment for you, but I can help you outline your ideas, or explain a concept you're stuck on.")

#STUDY TIMER SETUP
    elif "study mode" in c.lower() or "focus mode" in c.lower():
        speak(random.choice(study_quotes))
        speak("Study mode is on. If you want I can start a study timer.")

    elif "stop the timer" in c.lower() or "cancel the timer" in c.lower() or "cancel the alarm" in c.lower():
        timer_cancel.set()
        speak("Your study timer has been cancelled.")

    elif "timer" in c.lower():
        match = re.search(r"(\d+)\s*minute", c.lower())
        minutes = int(match.group(1)) if match else 25   # default is 25 minutes
        timer_cancel.clear()
        threading.Thread(target=study_timer, args=(minutes,), daemon=True).start()
        speak(f"Starting a {minutes} minute study timer. best of luck!")

#OPENING WEBSITES
    elif"open google" in c.lower():
        speak("Opening google")
        webbrowser.open("https://google.com")

    elif"open gmail" in c.lower():
        speak("opening gmail")
        webbrowser.open("https://mail.google.com")

    elif"open facebook" in c.lower():
        speak("opening facebook")
        webbrowser.open("https://facebook.com")
    
    elif"open youtube" in c.lower():
        speak("opening youtube")
        webbrowser.open("https://youtube.com")
    
    elif"open linkedin" in c.lower():
        speak("opening linkedin")
        webbrowser.open("https://linkedin.com")

    elif"open instagram" in c.lower():
        speak("opening instagram")
        webbrowser.open("https://www.instagram.com")

    elif"open ncert" in c.lower():
        speak("opening N C E R T")
        webbrowser.open("https://ncert.nic.in/textbook.php ")


#PLAYING SONGS FROM THE PRE-LOADED MUSIC LIBRARY
    elif c.lower().startswith("play"):
        if " " not in c:    #Guarding from crash if song is not in the library
            speak("Sorry, the song is not in my library")
            return
        
        song = c.lower().split(" ",1)[1]
        if song in ("my favorite song", "my favourite song"):
            song = memory.get("favorite song", "").lower()
        print("Looking for song:", song)
        link = music_library.music.get(song)
        if link:
            webbrowser.open(link)
            speak(f"playing {song}")
        else:
            speak("I could not find that song")

#OPENING NEWS
    elif "bbc news" in c.lower():
        speak("opening B B C news")
        webbrowser.open("https://www.bbc.com/")

    elif "cnn news" in c.lower():
        speak("opening  C N N news")
        webbrowser.open("https://edition.cnn.com/")

    elif "ndtv news" in c.lower():
        speak("opening N D T V news")
        webbrowser.open("https://www.ndtv.com/")

    elif "nobel prize" in c.lower():
        speak("opening the official list of nobel prize winners")
        webbrowser.open("https://www.nobelprize.org/all-nobel-prizes-2026/")


#OPENING WEBSITE OF OUR SCHOOL
    elif "school" in c.lower():#PM SHRI KENDRIYA VIDYALAYA ANDREWS GANJ
        speak("opening the official website of PM SHRI K V A G")
        webbrowser.open("https://andrewsganj.kvs.ac.in/en/")

 #OPENING STUDY FILES AND FOLDERS
    elif c.lower().startswith("open"):
    # elif "file" in c.lower() or "folder" in c.lower():
        name = c.lower().split(" ", 1)[1]
        path = study_library.study.get(name)
        if not path:
            speak("I could not find that in my study library at this very moment sir")
        elif not os.path.exists(path):
            speak("That file or folder seems to be missing sir ")
        else:
            speak(f"Opening {name} study materials")
            os.startfile(path)   # opens PDFs in your default viewer and folders in Explorer

    else:
        #let open ai handle the request of the user
        if OpenAI and OPENAI_API_KEY:
            try:
                speak(ai_process(c))
            except Exception as e:
                print("AI error:", repr(e))
                speak("Sorry sir, with an missing A P I, I could not reach my AI brain right now.")
        else:
            speak("Sorry, I cannot answer that yet sir")


#THE WAKE-WORD LOOP (moved into a function so it can run in the background)
def assistant_loop(r):
    speak("Jarvis Activated!")
    speak_quietly("IMPORTANT ADVISORY: The memory of jarvis can be acess by anyone using your computer, so do not forget to reset the memory if you think anyone else can acess your computer!")

    while interface.running:      # was: while True (stops when you close the HUD window)

        print("Recognizing...!")
        interface.set_state("listening")
        interface.log("Listening for the wake word...")
        try:
            with sr.Microphone() as source:
                # recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("Listening...!")
                audio = r.listen(source, timeout=5, phrase_time_limit=4)
            word = r.recognize_google(audio)

            if "jarvis" in word.lower():
                speak("yes sir ")
                #Listen for command
                with sr.Microphone() as source:
                    print("JARVIS ACTIVE...!")
                    interface.set_state("listening")
                    interface.log("Jarvis active... speak now")
                    audio = r.listen(source, timeout=5, phrase_time_limit=10)
                command = r.recognize_google(audio)
                print("Command", command)
                processCommand(command)

        except sr.WaitTimeoutError:
            pass  #no command, then loop again

        except sr.UnknownValueError:
            pass  #if speech did not understand

        except Exception as e: #to trace where error occured during execution
            print("Error:", e)
            interface.log("Error: " + str(e))
            traceback.print_exc()

        interface.set_state("idle")

if __name__ == "__main__":
        #"Listen for the wake word "JARVIS""
        # by obtaining audio from the microphone
        r = sr.Recognizer()

        #"AUTOMATIC CALIBRATION OF CATCHING FREQUENCY WITH NOISE PRESENT AT STARTUP"

        # with sr.Microphone() as source:
        #     r.adjust_for_ambient_noise(source, duration=1)
        # r.energy_threshold = max(r.energy_threshold * 4, 40)   # a safe margin above the room noise
        # r.dynamic_energy_threshold = False
        # print("Energy threshold:", r.energy_threshold)


        #"MANUAL CALIBRATION OF CATCHING FREQUENCY OF COMMAND"

        r.dynamic_energy_threshold = False
        r.energy_threshold = 50   #lower = more sensitive
        
         # start the assistant in the background...
        threading.Thread(target=assistant_loop, args=(r,), daemon=True).start()

        # ...and open the HUD window (must be last, it blocks until you close it)
        interface.run()


