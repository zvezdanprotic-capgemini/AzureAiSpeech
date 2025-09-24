import os
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()
subscription=os.environ.get('AZURE_SPEECH_KEY')
endpoint=os.environ.get('AZURE_SPEECH_ENDPOINT')
print(f"Using endpoint: {endpoint} and subscription: {subscription}")

def recognize_from_microphone():
    # This example requires environment variables named "SPEECH_KEY" and "ENDPOINT"
    # Replace with your own subscription key and endpoint, the endpoint is like : "https://YourServiceRegion.api.cognitive.microsoft.com"
   
    speech_translation_config = speechsdk.translation.SpeechTranslationConfig(subscription=subscription, endpoint=endpoint)
    speech_translation_config.speech_recognition_language="en-US"

    to_language ="it"
    speech_translation_config.add_target_language(to_language)

    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

    translation_recognizer = speechsdk.translation.TranslationRecognizer(translation_config=speech_translation_config, audio_config=audio_config)

    print("Speak into your microphone.")
    translation_recognition_result = translation_recognizer.recognize_once_async().get()

    if translation_recognition_result.reason == speechsdk.ResultReason.TranslatedSpeech:
        print("Recognized: {}".format(translation_recognition_result.text))
        print("""Translated into '{}': {}""".format(
            to_language, 
            translation_recognition_result.translations[to_language]))
    elif translation_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(translation_recognition_result.no_match_details))
    elif translation_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = translation_recognition_result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
            print("Did you set the speech resource key and endpoint values?")

def recognize_from_file(filename, from_language, to_language):
    """
    Recognizes speech from an audio file and translates it to the specified language.
    Returns a tuple containing (original_text, translated_text)
    """
    speech_translation_config = speechsdk.translation.SpeechTranslationConfig(subscription=subscription, endpoint=endpoint)
    speech_translation_config.speech_recognition_language=from_language
    speech_translation_config.add_target_language(to_language)

    audio_config = speechsdk.audio.AudioConfig(filename=filename)
    translation_recognizer = speechsdk.translation.TranslationRecognizer(translation_config=speech_translation_config, audio_config=audio_config)

    print(f"Processing audio file: {filename}")
    translation_recognition_result = translation_recognizer.recognize_once_async().get()
    
    original_text = ""
    translated_text = ""

    if translation_recognition_result.reason == speechsdk.ResultReason.TranslatedSpeech:
        original_text = translation_recognition_result.text
        translated_text = translation_recognition_result.translations[to_language]
        
        print("Recognized: {}".format(original_text))
        print("Translated into '{}': {}".format(to_language, translated_text))
        
        return original_text, translated_text
    
    elif translation_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        error_msg = "No speech could be recognized: {}".format(translation_recognition_result.no_match_details)
        print(error_msg)
        return "", error_msg
    
    elif translation_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = translation_recognition_result.cancellation_details
        error_msg = "Speech Recognition canceled: {}".format(cancellation_details.reason)
        print(error_msg)
        
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            error_details = "Error details: {}".format(cancellation_details.error_details)
            print(error_details)
            return "", f"{error_msg}: {error_details}"
        
        return "", error_msg



# Test the function
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_file = sys.argv[1]  # Get filename from command line
    else:
        test_file = "test_audio.wav"  # Default test file
        
    print(f"Testing speech recognition and translation with file: {test_file}")
    
    if os.path.exists(test_file):
        original, translation = recognize_from_file(test_file, "en-US", "es")
        print("\nResults:")
        print(f"Original text: {original}")
        print(f"Translated text: {translation}")
    else:
        print(f"Error: Test file '{test_file}' not found. Please provide a valid audio file path.")
        print("Usage: python speech_translation.py [path_to_audio_file]")