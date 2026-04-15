🎙️ CleanSpeak

CleanSpeak is an AI-powered audio processing pipeline that removes noise, converts speech to text, and filters inappropriate content to produce clean and usable outputs.

🚀 Features
🔊 Audio Noise Reduction
Removes background noise and enhances speech clarity
Built using Librosa, Noisereduce, and SciPy
🧠 Speech-to-Text (ASR)
Converts audio into text using OpenAI Whisper
🧹 Profanity Filtering
Detects and removes or replaces inappropriate words
⚙️ Modular Pipeline
Structured components for easy modification and scalability
🏗️ Project Structure

CleanSpeak/
│
├── main.py # Main pipeline controller
├── audio_cleaner.py # Noise reduction and preprocessing
├── transcriber.py # Speech-to-text using Whisper
├── word_filter.py # Profanity filtering logic
├── accuracy_test.py # Evaluation and testing
├── requirements.txt # Dependencies
└── README.md # Documentation

⚙️ How It Works

Audio Input
↓
Noise Reduction (Librosa, Noisereduce)
↓
Speech Recognition (Whisper)
↓
Text Filtering (Profanity Removal)
↓
Clean Output

🛠️ Installation
Clone the repository

  git clone https://github.com/Jeyxnth/CleanSpeak.git
  
  cd CleanSpeak
  
  Install dependencies
  
  pip install -r requirements.txt

Install FFmpeg (Required)
Windows: Download from https://ffmpeg.org/download.html
Add FFmpeg to system PATH
▶️ Usage

Run the main pipeline:

  python main.py

You can modify the input audio file inside the script or extend the project for API-based usage.

📊 Use Cases

🎧 Call center transcription
🗣️ Voice assistant preprocessing
🎥 Audio/video content moderation
📚 Meeting transcription tools
🔒 Safe communication systems

⚠️ Limitations

Rule-based filtering may miss contextual or nuanced language
Transcription accuracy depends on audio quality
Not optimized for real-time streaming or large-scale deployment
🔮 Future Improvements
🤖 Context-aware AI-based toxicity detection
⚡ Real-time audio processing
🔁 Streaming support
📈 Confidence-based filtering
🧠 Advanced deep learning noise reduction (e.g., DeepFilterNet)
🤝 Contributing

Contributions are welcome! Feel free to fork this repository and submit a pull request.

📄 License

This project is open-source and available under the MIT License.

👨‍💻 Author

Jeyanth S
GitHub: https://github.com/Jeyxnth

⭐ Support

If you found this project useful, consider giving it a ⭐ on GitHub!
