import aiohttp
import edge_tts
#from structure import DEFAULT_ELEVEN_LABS_VOICE


async def generate_audio(text, filepath, voice, provider="edge", elevenlabs_key=None ):
    if provider == "elevenlabs" and elevenlabs_key and voice:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
        headers = {
            "xi-api-key": elevenlabs_key, 
            "Content-Type": "application/json"
        }
        payload = {
            "text": text, 
            "model_id": "eleven_multilingual_v2" 
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        with open(filepath, 'wb') as f:
                            f.write(await response.read())
                        return 
                    else:
                        print(f"ElevenLabs Error: {await response.text()}")
        except Exception as e:
            print(f"ElevenLabs Exception: {e}")

    # Fallback to Edge TTS
    communicate = edge_tts.Communicate(text, voice, rate="-10%")
    await communicate.save(filepath)