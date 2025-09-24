# Speech Analysis App

A full-stack application for recording, transcribing, and translating speech using Azure AI Speech and Azure Translator services.

## Features
- Record audio from your browser and send to backend
- Transcribe speech to text using Azure AI Speech
- Translate transcribed text to any supported language using Azure Translator
- Modern React frontend and FastAPI backend

## Technologies Used
- React (frontend)
- FastAPI (backend)
- Azure Cognitive Services: Speech, Translator
- Python, JavaScript

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/zvezdanprotic-capgemini/AzureAiSpeech.git
cd AzureAiSpeech
```

### 2. Backend Setup
```bash
cd backend
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Fill in your Azure credentials
```

#### Start the backend server
```bash
python main.py
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm start
```

### 4. Environment Variables
- All secrets and configuration go in `backend/.env` (see `.env.example` for template)
- Never commit your real `.env` file!

### 5. Usage
- Open the frontend in your browser (default: http://localhost:3000)
- Record your voice, select a target language, and submit
- View transcription and translation results instantly

## File Structure
```
AzureAiSpeech/
├── backend/
│   ├── main.py
│   ├── speech_translation.py
│   ├── requirements.txt
│   ├── .env.example
│   └── ...
├── frontend/
│   ├── src/
│   │   └── App.js
│   ├── public/
│   │   └── index.html
│   └── ...
├── .gitignore
└── README.md
```

## Security & Best Practices
- `.env` and all temp files are gitignored
- Use `.env.example` for sharing config templates
- Do not share your Azure keys publicly

## License
MIT

## Author
[zvezdanprotic-capgemini](https://github.com/zvezdanprotic-capgemini)
