import requests
import io
from pydantic import BaseModel, Field
from cat.log import log
from cat.mad_hatter.decorators import hook, plugin
import base64


class Settings(BaseModel):
    url_model: str = Field(
        title="url model",
        description="The name of the container for OpenAI's transcription model.",
        default="http://openai-whisper-asr-webservice:9000",
    )
    audio_key: str = Field(
        title="Audio Key",
        description="The name of the json field for the WebSocket message sent from the user in order to recognize your audio. Defaults to 'audio_key'.",
        default="audio_key",
    )
    language: str = Field(
        title="Language",
        description="The language of the audio file. Defaults to 'en'.",
        default="en",
    )
@plugin
def settings_schema():
    return Settings.schema()


def decode_base64_audio(audio: str) -> bytes:
    """Decode a base64 encoded audio file."""
    return base64.b64decode(audio)


def transcript(audio_file, url, language):

    name_file = audio_file[0]  # Get the name of the file
    audio_body = audio_file[1]  # Get the file
    type_file = audio_file[2]  # Get the type of the file
    file_size = len(audio_body)

    if file_size > 25 * 1000000:  # Check file size
        return "Over 25MB? The audio shouldn't be this large."
    
    headers = {
        "accept": "application/json",
    }
    params = {
        "encode": "true",
        "task": "transcribe",
        "language": language,
        "word_timestamps": "false",
        "output": "json",
    }


    files = {
        "audio_file": (name_file, audio_body, type_file),
    }

    try:

        response = requests.post(
            url + "/asr", params=params, headers=headers, files=files
        )

    except requests.exceptions.ConnectionError as e:
        print("I'm sorry, I couldn't connect to the server. Please try again later")
        print(e)
        return "I'm sorry, I couldn't connect to the server. Please try again later"


    if response.ok:
        # response.raise_for_status()  # Ensure we notice bad responses
        json_response = response.json()

        return json_response["text"]

    else:
        print("Status Code ", response.status_code)
        return "I'm sorry, I couldn't transcribe the audio file. Please try again later"


@hook(priority=99)
def before_cat_reads_message(message: dict, cat) -> dict:
    settings = cat.mad_hatter.get_plugin().load_settings()

    try:
        if settings == {}:
            log.error("No configuration found for Local Whisper Cat")
            raise Exception("No configuration found for Local Whisper Cat reverting to default settings.")

    
    except Exception as e:
        
        default_settings = Settings()
        # Default settings loaded
        # Imposta i valori di default
        settings = {
            "url_model": default_settings.url_model,
            "audio_key": default_settings.audio_key,
            "language": default_settings.language,
        }

        
    
    
    if settings["audio_key"] not in message.keys():
        log.error("This message does not contain an audio file.")
        return message

    print("message[settings['audio_key']]: " + str(message[settings["audio_key"]]))
    if message[settings["audio_key"]] == "":
        log.error("The audio file path is empty.")
        return message

    received_blob = message[settings["audio_key"]]  # Get the file path from the message

    if "encodedBase64" in message.keys() and message["encodedBase64"] == True:
        print("Decodifico il file da base64")
        # decode the file from base64
        decoded_blob = decode_base64_audio(received_blob)
    else:
        print("File not in base64 or wrongly flagged") 

    file = io.BytesIO(decoded_blob)

    try:
        with file:
            data = file.read()
    except OSError as e:
        print(f"Error opening the file: {e}")

    name_file = message["audio_name"]  # Get the name of the file
    audio_body = data  # Get the file content
    type_file = message["audio_type"]  # Get the type of the file

    file = (name_file, audio_body, type_file)

    # Making the transcription
    transcription = transcript(
        file,
        url=settings["url_model"],
        language=settings["language"],
    )

    message["text"] = transcription
    return message
