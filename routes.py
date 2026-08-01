"""HTTP-Routen für die HTML-Oberfläche und die JSON-API."""

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from models.analysis import AnalysisResult
from service import analyze_log


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
router = APIRouter()

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
ALLOWED_SUFFIXES = {".log", ".txt"}


async def _read_log_file(upload: UploadFile) -> tuple[str, str]:
    """Validiert und liest eine kleine Text-Logdatei sicher ein."""

    filename = Path(upload.filename or "upload.log").name
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail="Erlaubt sind nur .log- und .txt-Dateien.")

    data = await upload.read(MAX_UPLOAD_BYTES + 1)
    await upload.close()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Die Datei darf maximal 2 MB gross sein.")
    if not data:
        raise HTTPException(status_code=400, detail="Die hochgeladene Datei ist leer.")
    if b"\x00" in data:
        raise HTTPException(status_code=400, detail="Die Datei scheint keine Textdatei zu sein.")

    try:
        return data.decode("utf-8"), filename
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="Die Datei muss UTF-8-kodierter Text sein.",
        ) from exc


@router.get("/", response_class=HTMLResponse)
async def start_page(request: Request) -> HTMLResponse:
    """Zeigt die Upload-Seite."""

    return templates.TemplateResponse(request=request, name="index.html")


@router.post("/analyze", response_class=HTMLResponse)
async def analyze_page(request: Request, log_file: UploadFile = File(...)) -> HTMLResponse:
    """Analysiert eine Datei und rendert das Resultat als HTML."""

    try:
        content, filename = await _read_log_file(log_file)
    except HTTPException as exc:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"error": exc.detail},
            status_code=exc.status_code,
        )

    result = analyze_log(content, filename)
    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={"result": result},
    )


@router.post("/api/analyze", response_model=AnalysisResult)
async def analyze_api(log_file: UploadFile = File(...)) -> AnalysisResult:
    """Liefert dasselbe Analyseergebnis als strukturiertes JSON."""

    content, filename = await _read_log_file(log_file)
    return analyze_log(content, filename)


@router.get("/api/health")
async def health() -> dict[str, str]:
    """Einfacher Health-Check für Entwicklung und Deployment."""

    return {"status": "ok"}
