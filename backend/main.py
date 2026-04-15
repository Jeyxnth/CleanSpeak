import os
import uuid
import shutil
import logging
import re
import librosa
import soundfile as sf
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from processing.transcriber import transcribe, preload_transcriber
from processing.word_filter import (
    get_filler_words, get_flagged_words, add_flagged_word
)

UPLOAD_DIR = "backend/temp/uploads"
ORIGINAL_DIR = "backend/temp/original"
CLEANED_DIR = "backend/temp/cleaned"
LEGACY_OUTPUT_DIR = "backend/temp/outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(ORIGINAL_DIR, exist_ok=True)
os.makedirs(CLEANED_DIR, exist_ok=True)
os.makedirs(LEGACY_OUTPUT_DIR, exist_ok=True)

app = FastAPI()
logger = logging.getLogger("clean_speech.pipeline")

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s"))
    logger.addHandler(handler)

logger.setLevel(logging.INFO)
logger.propagate = False


@app.on_event("startup")
async def preload_transcriber_model() -> None:
    try:
        model = preload_transcriber(model_name=_select_model("en"), language="en")
        logger.info("transcriber.preloaded model=%s", model)
    except Exception:
        logger.exception("transcriber.preload_failed")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUDIO_EXTENSIONS = {"mp3", "wav", "ogg", "m4a", "webm"}


def _normalize_mode(mode: str) -> str:
    normalized = (mode or "normal").strip().lower()
    if normalized not in {"normal", "clear"}:
        raise HTTPException(status_code=400, detail="mode must be either 'normal' or 'clear'.")
    return normalized


def _select_model(language: str) -> str:
    return "base.en" if language.lower().startswith("en") else "base"


def _load_as_wav(input_path: str, output_path: str, target_sr: int = 16000) -> None:
    audio, sr = librosa.load(input_path, sr=target_sr, mono=True)
    if audio.size == 0:
        raise ValueError("Uploaded audio has no samples")
    sf.write(output_path, audio, sr, format="WAV", subtype="PCM_16")


def _safe_audio_filename(filename: str) -> str:
    safe_name = os.path.basename(filename)
    if safe_name != filename or not safe_name.lower().endswith(".wav"):
        raise HTTPException(status_code=400, detail="Invalid audio filename")
    return safe_name


def clean_transcript(text: str) -> dict:
    original_words = len(text.split())

    # Remove stutters
    words = text.split()
    deduped = [words[0]] if words else []
    for i in range(1, len(words)):
        if words[i].lower() != words[i-1].lower():
            deduped.append(words[i])
    text = ' '.join(deduped)

    # Remove fillers
    fillers = [
        r'\buh+\b', r'\bum+\b', r'\bhmm+\b', r'\bhuh\b',
        r'\byou know\b', r'\bi mean\b', r'\bkind of\b',
        r'\bsort of\b', r'\bokay so\b', r'\bbasically\b',
    ]
    for p in fillers:
        text = re.sub(p, '', text, flags=re.IGNORECASE)
    text = re.sub(r' +', ' ', text).strip()

    # Censor profanity
    bad_words = [
        "damn","hell","crap","shit","fuck",
        "bastard","bitch","ass","idiot","stupid"
    ]
    censored_count = 0
    for word in bad_words:
        pat = r'\b' + re.escape(word) + r'\b'
        if re.search(pat, text, re.IGNORECASE):
            text = re.sub(pat, '[bleep]', text, flags=re.IGNORECASE)
            censored_count += 1

    cleaned_words = len(text.split())
    return {
        "cleaned_transcript": text,
        "fillers_removed": max(0, original_words - cleaned_words - censored_count),
        "words_censored": censored_count,
    }

@app.post("/process")
async def process_audio(
    file: UploadFile = File(...),
    mode: str = Form("normal"),
    apply_noise_reduction: bool = Form(False),
    language: str = Form("en"),
):
    ext = file.filename.split(".")[-1].lower()
    if ext not in AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported audio format.")

    selected_mode = _normalize_mode(mode)
    use_noise_reduction = bool(apply_noise_reduction)
    use_chunked_vad = False

    print(f"[API RECEIVED] apply_noise_reduction={use_noise_reduction}")

    job_id = str(uuid.uuid4())
    upload_path = os.path.join(UPLOAD_DIR, f"{job_id}.{ext}")
    original_filename = f"{job_id}.wav"
    original_path = os.path.join(ORIGINAL_DIR, original_filename)

    # Save upload
    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        _load_as_wav(upload_path, original_path, target_sr=16000)
    except Exception as e:
        if os.path.exists(upload_path):
            os.remove(upload_path)
        raise HTTPException(status_code=500, detail=f"Audio conversion failed: {e}")

    transcription_input = original_path
    transcription_model = _select_model(language)

    logger.info(
        "transcription.start job_id=%s mode=%s model=%s noise_reduction=%s vad_chunking=%s language=%s filename=%s transcription_input=%s",
        job_id,
        selected_mode,
        transcription_model,
        use_noise_reduction,
        use_chunked_vad,
        language,
        file.filename,
        transcription_input,
    )

    # Transcribe
    try:
        raw_transcript = transcribe(
            transcription_input,
            model_name=transcription_model,
            language=language,
        )
    except Exception as e:
        logger.exception(
            "transcription.failed job_id=%s mode=%s model=%s noise_reduction=%s vad_chunking=%s language=%s",
            job_id,
            selected_mode,
            transcription_model,
            use_noise_reduction,
            use_chunked_vad,
            language,
        )
        if os.path.exists(upload_path):
            os.remove(upload_path)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

    cleaned = clean_transcript(raw_transcript)

    # Clean up upload
    if os.path.exists(upload_path):
        os.remove(upload_path)

    logger.info(
        "transcription.complete job_id=%s mode=%s model=%s noise_reduction_requested=%s vad_chunking=%s words_raw=%s words_cleaned=%s",
        job_id,
        selected_mode,
        transcription_model,
        use_noise_reduction,
        use_chunked_vad,
        len((raw_transcript or "").split()),
        len((cleaned.get("cleaned_transcript") or "").split()),
    )

    original_audio_url = f"/audio/original/{original_filename}"

    response = {
        "job_id": job_id,
        "transcript": raw_transcript,
        "original_transcript": raw_transcript,
        "mode": selected_mode,
        "noise_applied": use_noise_reduction,
        "chunked_vad_applied": False,
        "chunk_count": 1,
        "large_model_requested": False,
        "model_fallback_applied": False,
        "model_used": transcription_model,
        "raw_transcript": raw_transcript,
        "original_audio_url": original_audio_url,
        "cleaned_audio_url": None,
    }

    cleaned_transcript = cleaned["cleaned_transcript"]
    response["cleaned_transcript"] = cleaned_transcript
    response["fillers_removed"] = cleaned["fillers_removed"]
    response["words_censored"] = cleaned["words_censored"]
    response["cleaned_word_count"] = len(cleaned_transcript.split())
    response["original_word_count"] = len(raw_transcript.split())
    response["filler_count"] = response["fillers_removed"]
    response["flagged_count"] = response["words_censored"]

    return response

@app.get("/download/{job_id}")
def download_audio(job_id: str):
    cleaned_wav_path = os.path.join(CLEANED_DIR, f"{job_id}.wav")
    legacy_wav_path = os.path.join(LEGACY_OUTPUT_DIR, f"{job_id}.wav")
    legacy_mp3_path = os.path.join(LEGACY_OUTPUT_DIR, f"{job_id}.mp3")

    if os.path.exists(cleaned_wav_path):
        return FileResponse(cleaned_wav_path, media_type="audio/wav", filename=f"cleaned_{job_id}.wav")

    if os.path.exists(legacy_wav_path):
        return FileResponse(legacy_wav_path, media_type="audio/wav", filename=f"cleaned_{job_id}.wav")

    if os.path.exists(legacy_mp3_path):
        return FileResponse(legacy_mp3_path, media_type="audio/mpeg", filename=f"cleaned_{job_id}.mp3")

    raise HTTPException(status_code=404, detail="File not found.")


@app.get("/audio/original/{filename}")
def get_original_audio(filename: str):
    safe_name = _safe_audio_filename(filename)
    original_path = os.path.join(ORIGINAL_DIR, safe_name)
    if not os.path.exists(original_path):
        raise HTTPException(status_code=404, detail="Original audio not found.")
    return FileResponse(original_path, media_type="audio/wav", filename=safe_name)


@app.get("/audio/cleaned/{filename}")
def get_cleaned_audio(filename: str):
    safe_name = _safe_audio_filename(filename)
    cleaned_path = os.path.join(CLEANED_DIR, safe_name)
    if not os.path.exists(cleaned_path):
        raise HTTPException(status_code=404, detail="Cleaned audio not found.")
    return FileResponse(cleaned_path, media_type="audio/wav", filename=safe_name)

@app.get("/words/filler")
def list_filler_words():
    return {"filler_words": get_filler_words()}

@app.get("/words/flagged")
def list_flagged_words():
    return {"flagged_words": get_flagged_words()}

@app.post("/words/flagged/add")
def add_flagged(word: str):
    if not word or not word.strip():
        raise HTTPException(status_code=400, detail="Word must not be empty.")
    add_flagged_word(word.strip())
    return {"flagged_words": get_flagged_words()}
