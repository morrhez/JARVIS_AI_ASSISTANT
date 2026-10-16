import speech_recognition as sr

r = sr.Recognizer()
with sr.Microphone() as source:
    print("Stay quiet for 2 seconds...")
    r.adjust_for_ambient_noise(source, duration=2)
    print("Room noise level:", r.energy_threshold)