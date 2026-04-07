import tempfile
import uuid
from pathlib import Path
from threading import Thread

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse, PlainTextResponse  # noqa: E402

from transcribe import format_srt, format_txt, transcribe  # noqa: E402

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# In-memory job store
jobs: dict[str, dict] = {}


def run_transcription(job_id: str, audio_path: str, language: str = "ko"):
    def on_progress(stage: str, message: str):
        jobs[job_id]["stage"] = stage
        jobs[job_id]["message"] = message

    try:
        on_progress("starting", "Preparing...")
        segments = transcribe(
            audio_path, progress_callback=on_progress, diarize=True, language=language
        )
        jobs[job_id]["status"] = "done"
        jobs[job_id]["segments"] = segments
        jobs[job_id]["result"] = format_txt(segments)
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["message"] = str(e)
    finally:
        Path(audio_path).unlink(missing_ok=True)


@app.post("/transcribe")
async def start_transcription(file: UploadFile, language: str = "ko"):
    job_id = str(uuid.uuid4())

    suffix = Path(file.filename).suffix if file.filename else ".wav"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(await file.read())
    tmp.close()

    jobs[job_id] = {
        "status": "processing",
        "stage": "uploading",
        "message": "File uploaded",
    }
    Thread(
        target=run_transcription, args=(job_id, tmp.name, language), daemon=True
    ).start()

    return {"job_id": job_id}


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    return job


@app.get("/export/{job_id}/{fmt}")
async def export_transcript(job_id: str, fmt: str):
    job = jobs.get(job_id)
    if not job or job.get("status") != "done":
        return JSONResponse(
            status_code=404, content={"error": "Job not found or not complete"}
        )

    segments = job["segments"]

    if fmt == "txt":
        return PlainTextResponse(
            format_txt(segments),
            headers={"Content-Disposition": "attachment; filename=transcript.txt"},
        )
    elif fmt == "srt":
        return PlainTextResponse(
            format_srt(segments),
            headers={"Content-Disposition": "attachment; filename=transcript.srt"},
        )
    elif fmt == "json":
        return JSONResponse(
            content=segments,
            headers={"Content-Disposition": "attachment; filename=transcript.json"},
        )
    else:
        return JSONResponse(
            status_code=400, content={"error": "Format must be txt, srt, or json"}
        )
