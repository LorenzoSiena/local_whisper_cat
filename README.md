# Local Whisper Cat
[![awesome plugin](https://custom-icon-badges.demolab.com/static/v1?label=&message=awesome+plugin&color=F4F4F5&style=for-the-badge&logo=cheshire_cat_black)](https://)

A plugin to transcript locally on your gpu/cpu, audio files to text.

![logo](https://github.com/LorenzoSiena/local_whisper_cat/blob/main/local_whisper_cat_logo.png)

## How it works

This plugin communicates with a local container running an api service to transcript audio files to text.

In the settings panel you can set the location of the container and the audio_key . 

Should be agnostic but in practice I am referring to [Whisper ASR Webservice](https://github.com/ahmetoner/whisper-asr-webservice)

## How to setup

Choose the url model

    "http://openai-whisper-asr-webservice:9000" by default

Choose an Audio key field for your Websocket message

    "audio_key" by default

Choose a language

    "en" by default


## How to send audio files

Your client should send a message with the following fields: text, user_id, audio_key, audio_type, audio_name, encodedBase64. 

The audio_key field should contain the base64 encoded audio file.
like the next example:

    your_json_fields = {
        text='',
        user_id='user69',
        audio_key: "",
        audio_type: "
        "audio/ogg"
        ",audio_name: 'msg45430839-160807.ogg',
        encodedBase64: True,
        }
For convenience you can use a compatible Python client [Chatty!](https://github.com/LorenzoSiena/chatty) in order to send 10 second audio in the right format.

Obviously you must have set the [nvidia-container-toolkit](https://github.com/NVIDIA/nvidia-container-toolkit) and have an adequate video card

Obviously you need a running container with whisper-asr-webservice

The accepted audio formats are: `mp3`, `wav`, `ogg`,`mpeg`, `mp4`(depending on the container settings).

# Example of a full local istance with ollama and nvidia container with docker-compose

```yaml
networks:
    fullcat-network:
services:
    cheshire-cat-core:
        build:
            context: ./core
        container_name: cheshire_cat_core
        depends_on:
            - cheshire-cat-vector-memory
            - ollama
            - openai-whisper-asr-webservice
        environment:
            - PYTHONUNBUFFERED=1
            - WATCHFILES_FORCE_POLLING=true
            - CORE_HOST=${CORE_HOST:-localhost}
            - CORE_PORT=${CORE_PORT:-1865}
            - QDRANT_HOST=${QDRANT_HOST:-cheshire_cat_vector_memory}
            - QDRANT_PORT=${QDRANT_PORT:-6333}
            - CORE_USE_SECURE_PROTOCOLS=${CORE_USE_SECURE_PROTOCOLS:-}
            - API_KEY=${API_KEY:-}
            - LOG_LEVEL=${LOG_LEVEL:-DEBUG}
            - DEBUG=${DEBUG:-true}
            - SAVE_MEMORY_SNAPSHOTS=${SAVE_MEMORY_SNAPSHOTS:-false}
        ports:
            - ${CORE_PORT:-1865}:80
        volumes:
            - ./cat/static:/app/cat/static
            - ./cat/public:/app/cat/public
            - ./cat/plugins:/app/cat/plugins
            - ./cat/metadata.json:/app/metadata.json
        restart: unless-stopped
        networks:
            - fullcat-network
            
    cheshire-cat-vector-memory:
        image: qdrant/qdrant:latest
        container_name: cheshire_cat_vector_memory
        expose:
            - 6333
        volumes:
            - ./cat/long_term_memory/vector:/qdrant/storage
        restart: unless-stopped
        networks:
            - fullcat-network
            
    ollama:
        container_name: ollama_cat
        image: ollama/ollama:latest
        volumes:
            - ./ollama:/root/.ollama
        expose:
            - 11434
        environment:
            - gpus=all
        deploy:
            resources:
                reservations:
                    devices:
                        - driver: nvidia
                          count: 1
                          capabilities:
                              - gpu
        networks:
            - fullcat-network
            
    openai-whisper-asr-webservice:
        deploy:
            resources:
                reservations:
                    devices:
                        - driver: nvidia
                          count: all
                          capabilities:
                              - gpu
        ports:
            - 9000:9000
        expose:
            - 9000
        environment:
            - ASR_MODEL=base
            - ASR_ENGINE=openai_whisper
        image: onerahmet/openai-whisper-asr-webservice:latest-gpu
        networks:
            - fullcat-network

```

