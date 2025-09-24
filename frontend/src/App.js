import React, { useState, useRef } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';


function App() {
  const [recording, setRecording] = useState(false);
  const [audioURL, setAudioURL] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [targetLanguage, setTargetLanguage] = useState('es');
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioContextRef = useRef(null);

  // Function to convert audio buffer to WAV format (16kHz, 16-bit, mono)
  const audioBufferToWav = (buffer, sampleRate = 16000) => {
    const numberOfChannels = 1; // Mono
    const length = buffer.length * numberOfChannels * 2; // 16-bit = 2 bytes per sample
    const arrayBuffer = new ArrayBuffer(44 + length);
    const view = new DataView(arrayBuffer);

    // WAV header
    const writeString = (offset, string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };

    writeString(0, 'RIFF'); // ChunkID
    view.setUint32(4, 36 + length, true); // ChunkSize
    writeString(8, 'WAVE'); // Format
    writeString(12, 'fmt '); // Subchunk1ID
    view.setUint32(16, 16, true); // Subchunk1Size
    view.setUint16(20, 1, true); // AudioFormat (PCM)
    view.setUint16(22, numberOfChannels, true); // NumChannels
    view.setUint32(24, sampleRate, true); // SampleRate
    view.setUint32(28, sampleRate * numberOfChannels * 2, true); // ByteRate
    view.setUint16(32, numberOfChannels * 2, true); // BlockAlign
    view.setUint16(34, 16, true); // BitsPerSample
    writeString(36, 'data'); // Subchunk2ID
    view.setUint32(40, length, true); // Subchunk2Size

    // Convert float samples to 16-bit PCM
    let offset = 44;
    for (let i = 0; i < buffer.length; i++) {
      const sample = Math.max(-1, Math.min(1, buffer[i])); // Clamp to [-1, 1]
      const intSample = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
      view.setInt16(offset, intSample, true);
      offset += 2;
    }

    return new Blob([arrayBuffer], { type: 'audio/wav' });
  };

  const getLanguageName = (code) => {
    const languages = {
      'es': 'Spanish',
      'fr': 'French', 
      'de': 'German',
      'it': 'Italian',
      'pt': 'Portuguese',
      'ja': 'Japanese',
      'ko': 'Korean',
      'zh': 'Chinese'
    };
    return languages[code] || code;
  };

  const handleRecordClick = async () => {
    if (recording) {
      // Stop recording
      mediaRecorderRef.current.stop();
      setRecording(false);
    } else {
      setError(null);
      setResults(null);
      setAudioURL(null);
      // Start recording
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            sampleRate: 16000,
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true
          }
        });

        // Create AudioContext for processing
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({
          sampleRate: 16000
        });

        const mediaRecorder = new window.MediaRecorder(stream, {
          mimeType: 'audio/webm;codecs=opus'
        });
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) {
            audioChunksRef.current.push(e.data);
          }
        };

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          setAudioURL(URL.createObjectURL(audioBlob));
          
          // Convert to WAV format
          try {
            const arrayBuffer = await audioBlob.arrayBuffer();
            const audioBuffer = await audioContextRef.current.decodeAudioData(arrayBuffer);
            
            // Get audio data (convert to mono if needed)
            const audioData = audioBuffer.numberOfChannels > 1 
              ? audioBuffer.getChannelData(0) // Take first channel for mono
              : audioBuffer.getChannelData(0);
            
            // Convert to WAV
            const wavBlob = audioBufferToWav(audioData, 16000);
            sendAudioToBackend(wavBlob);
          } catch (error) {
            console.error('Error converting audio:', error);
            setError('Error processing audio. Please try again.');
          }
        };

        mediaRecorder.start();
        setRecording(true);
      } catch (err) {
        console.error('Microphone error:', err);
        setError('Microphone access denied or not available.');
      }
    }
  };

  const sendAudioToBackend = async (audioBlob) => {
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.wav');
      formData.append('target_language', targetLanguage);
      const response = await axios.post(`${API_BASE_URL}/analyze-audio`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000
      });
      setResults(response.data);
    } catch (err) {
      console.error('Backend error:', err);
      setError('Error analyzing audio. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <div className="container">
        <h1>🎤 Speech Analysis with Azure AI Speech</h1>
        <p>Record your voice and get transcription and translation using Azure AI Speech.</p>

        <div style={{ marginBottom: '1em' }}>
          <label htmlFor="language-select">Choose translation language: </label>
          <select 
            id="language-select"
            value={targetLanguage} 
            onChange={(e) => setTargetLanguage(e.target.value)}
            style={{ padding: '0.5em', marginLeft: '0.5em' }}
          >
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="de">German</option>
            <option value="it">Italian</option>
            <option value="pt">Portuguese</option>
            <option value="ja">Japanese</option>
            <option value="ko">Korean</option>
            <option value="zh">Chinese</option>
          </select>
        </div>

        <button
          onClick={handleRecordClick}
          style={{
            backgroundColor: recording ? 'red' : 'green',
            color: 'white',
            padding: '1em 2em',
            fontSize: '1.2em',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            marginBottom: '1em',
          }}
        >
          {recording ? 'Stop Recording' : 'Start Recording'}
        </button>

        {audioURL && (
          <div style={{ marginBottom: '1em' }}>
            <audio controls src={audioURL} />
          </div>
        )}

        {loading && (
          <div className="loading">
            <div className="loading-spinner"></div>
            <div>Processing your audio with Azure AI Speech...</div>
          </div>
        )}

        {error && (
          <div className="error">
            {error}
          </div>
        )}

        {results && (
          <div className="results">
            <h2>Analysis Results</h2>
            <div style={{ marginBottom: '1em' }}>
              <strong>Transcription:</strong> 
              <div style={{ marginTop: '0.5em', padding: '0.5em', backgroundColor: '#000000', color: '#ffffff', borderRadius: '4px' }}>
                {results.transcription}
              </div>
            </div>
            <div>
              <strong>Translation ({getLanguageName(results.target_language || targetLanguage)}):</strong>
              <div style={{ marginTop: '0.5em', padding: '0.5em', backgroundColor: '#000000', color: '#ffffff', borderRadius: '4px' }}>
                {results.translation}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
