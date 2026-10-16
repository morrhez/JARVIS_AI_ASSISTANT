import speech_recognition as sr

r = sr.Recognizer()

try:
    with sr.Microphone() as source:
        print("Adjusting for background noise...")
        r.adjust_for_ambient_noise(source, duration=1)

        print("Speak now!")
        audio = r.listen(source, timeout=10)

        print("Audio captured successfully!")

except sr.WaitTimeoutError:
    print("No speech detected within 10 seconds.")

except Exception as e:
    print("Error:", repr(e))