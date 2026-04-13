My research to convert EPUB to a Reader app

- Convert EPUB to MP3
- PWA App to read Epub
- Read a EPUB and convert to M4B using built in Apple Voice and create a MP3
- It automatically ignore pages numbers, etc. 
- https://www.google.com/search?q=python+text+to+voice+apple+speach&rlz=1C5CHFA_enAU890AU890&oq=python+text+to+voice+apple+speach&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIHCAEQIRigATIHCAIQIRigATIHCAMQIRigATIHCAQQIRigATIHCAUQIRiPAtIBCDY0MTFqMGo3qAIAsAIA&sourceid=chrome&ie=UTF-8#fpstate=ive&vld=cid:090d345c,vid:92Vy3N4VorI,st:170


```
# Simple macOS TTS using subprocess
import subprocess

def speak_macos(text):
    subprocess.call(['say', text])

speak_macos("Hello from Apple speech")

```

```
import os
os.system("say 'Hello World'")

```

```
import pyttsx3
engine = pyttsx3.init()
engine.say("Hello, this is offline speech.")
engine.runAndWait()

```
