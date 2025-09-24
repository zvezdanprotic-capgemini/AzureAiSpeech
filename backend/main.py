from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import io
import uuid
import json
import requests
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
import logging
# Import the speech translation functionality
from speech_translation import recognize_from_file


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Speech Analysis API", description="API for analyzing speech using Azure AI Speech")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # React ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_speech_config():
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION")
    if not speech_key or not speech_region:
        raise HTTPException(status_code=500, detail="Azure Speech credentials not configured.")
    return speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)

def translate_text(text, target_language, source_language="en"):
    """
    Translate text using Azure Translator REST API
    Based on the translate.py example
    """
    key = os.getenv("AZURE_TRANSLATOR_KEY")
    endpoint = os.getenv("AZURE_TRANSLATOR_ENDPOINT")
    region = os.getenv("AZURE_TRANSLATOR_REGION")
    
    if not key or not endpoint:
        raise HTTPException(status_code=500, detail="Azure Translator credentials not configured.")
    
    # Disable SSL verification warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    path = '/translate'
    constructed_url = endpoint + path
    
    params = {
        'api-version': '3.0',
        'from': source_language,
        'to': [target_language]
    }
    
    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }
    
    # Add region header if available
    if region:
        headers['Ocp-Apim-Subscription-Region'] = region
    
    body = [{'text': text}]
    
    try:
        request = requests.post(
            constructed_url, 
            params=params, 
            headers=headers, 
            json=body,
            verify=False
        )
        request.raise_for_status()  # Raise an exception for bad status codes
        response = request.json()
        
        if response and len(response) > 0 and 'translations' in response[0]:
            return response[0]['translations'][0]['text']
        else:
            logger.warning("No translation result received")
            return "Translation failed"
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Translation request error: {e}")
        raise HTTPException(status_code=500, detail=f"Translation request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")


@app.get("/")
async def root():
    return {"message": "Speech Analysis API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Speech Analysis API"}



# New endpoint for audio analysis
@app.post("/analyze-audio")
async def analyze_audio(audio: UploadFile = File(...), target_language: str = Form("es")):
    """
    Analyze uploaded audio: transcribe and translate using Azure AI Speech and Translator
    """
    try:
        if not audio.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        audio_data = await audio.read()
        if len(audio_data) > 120 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Audio size must be less than 120MB")

        # Speech to text
        speech_config = get_speech_config()
        speech_config.speech_recognition_language = "en-US"  # Set language
        
        # Save audio data to temporary WAV file for processing
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        try:
            # Use the recognize_from_file function from speech_translation.py 
            # for combined speech recognition and translation in one step
            logger.info(f"Starting speech recognition and translation for WAV file: {temp_file_path}")
            
            try:
                # Try the new function first (combined recognition and translation)
                transcription, translation = recognize_from_file(temp_file_path, "en-US", target_language)
                logger.info(f"Speech recognized: {transcription}")
                logger.info(f"Translation to {target_language}: {translation}")
                
                # If either result is empty or contains an error message, throw an exception to fall back
                if not transcription or not translation or translation.startswith("Speech Recognition canceled") or translation.startswith("No speech could be recognized"):
                    logger.warning("Speech recognition using recognize_from_file failed or returned empty results, falling back to separate methods")
                    raise Exception("Empty results from speech_translation module")
                    
            except Exception as speech_translation_error:
                # Fall back to the original method if the new one fails
                logger.warning(f"Falling back to original speech recognition method: {str(speech_translation_error)}")
                
                # Create audio config from WAV file
                audio_input = speechsdk.AudioConfig(filename=temp_file_path)
                recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)
                
                result = recognizer.recognize_once()
                
                if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    transcription = result.text
                    logger.info(f"Speech recognized (fallback): {transcription}")
                elif result.reason == speechsdk.ResultReason.NoMatch:
                    logger.warning("No speech could be recognized")
                    raise HTTPException(status_code=400, detail="No speech could be recognized. Please try speaking louder or closer to the microphone.")
                elif result.reason == speechsdk.ResultReason.Canceled:
                    cancellation_details = speechsdk.CancellationDetails(result)
                    error_msg = f"Speech recognition canceled: {cancellation_details.reason}"
                    if cancellation_details.error_details:
                        error_msg += f". Details: {cancellation_details.error_details}"
                    logger.error(error_msg)
                    raise HTTPException(status_code=500, detail=error_msg)
                else:
                    raise HTTPException(status_code=500, detail="Speech recognition failed with unknown reason")
                
                # Use the original translate_text function as fallback
                if transcription.strip():  # Only translate if we have text
                    try:
                        translation = translate_text(transcription, target_language, "en")
                        logger.info(f"Translation to {target_language} (fallback): {translation}")
                    except HTTPException as http_error:
                        logger.error(f"Translation HTTP error: {http_error.detail}")
                        translation = f"Translation error: {http_error.detail}"
                    except Exception as translate_error:
                        logger.error(f"Translation error: {translate_error}")
                        translation = f"Translation error: {str(translate_error)}"
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except OSError as e:
                logger.warning(f"Could not delete temporary file {temp_file_path}: {e}")

        return JSONResponse(content={
            "transcription": transcription,
            "translation": translation,
            "target_language": target_language
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    if debug:
        # Use import string for reload mode
        uvicorn.run("main:app", host=host, port=port, reload=True)
    else:
        # Use app object for production
        uvicorn.run(app, host=host, port=port, reload=False)
