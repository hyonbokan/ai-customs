"""
TradePDFExtractor
=================
High-quality PDF → structured-JSON converter for customs documents.
• Docling ≥ 0.13   – layout, tables
• Tesseract-5      – primary multilingual OCR
• EasyOCR (opt.)   – fallback OCR
• PyMuPDF (fitz)   – PDF to image conversion (replaces pdf2image/poppler)
"""

# ── stdlib ────────────────────────────────────────────────────────────────
import io
import json
import os
import statistics
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── third-party ───────────────────────────────────────────────────────────
import pytesseract
from PIL import Image

try:
    import fitz  # PyMuPDF

    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
try:
    from easyocr import Reader

    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False
try:
    import aiohttp

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

# ── local ─────────────────────────────────────────────────────────────────
from core.utils.logger import logger

# ── runtime configuration (override via import) ───────────────────────────
try:
    from config.pdf_config import pdf_config

    CFG = pdf_config.config
except Exception:

    class _Cfg:
        enable_tables = True
        enable_cell_matching = True
        enable_ocr = True
        # EasyOCR-style default codes
        ocr_languages = ["en", "ch_sim", "ar", "es", "fr", "ko", "ru", "th", "vi"]
        force_full_page_ocr = True
        timeout_seconds = 180
        max_file_size_mb = 50

    CFG = _Cfg()  # type: ignore[assignment]

# ── language maps ────────────────────────────────────────────────────────
LANG_MAP_TESS2EASY = {
    "eng": "en",
    "chi_sim": "ch_sim",
    "ara": "ar",
    "spa": "es",
    "fra": "fr",
    "kor": "ko",
    "rus": "ru",
    "tha": "th",
    "vie": "vi",
    "deu": "de",
    "jpn": "ja",
    "ita": "it",
    "por": "pt",
    "nld": "nl",
    "pol": "pl",
    # … extend if needed
}
LANG_MAP_EASY2TESS = {v: k for k, v in LANG_MAP_TESS2EASY.items()}


# ── result model ──────────────────────────────────────────────────────────
@dataclass
class DocumentParseResult:
    success: bool
    text_content: str = ""
    tables: List[Dict[str, Any]] | None = None
    metadata: Dict[str, Any] | None = None
    page_content: List[Dict[str, Any]] | None = None
    error_message: str | None = None

    def __post_init__(self):
        self.tables = self.tables or []
        self.metadata = self.metadata or {}
        self.page_content = self.page_content or []


# ── Docling converter cache ───────────────────────────────────────────────
def _build_opts():
    from docling.datamodel.pipeline_options import (
        AcceleratorDevice,
        AcceleratorOptions,
        EasyOcrOptions,
        PdfPipelineOptions,
        TableFormerMode,
    )

    opts = PdfPipelineOptions()
    opts.images_scale = 2.0
    opts.generate_page_images = True
    opts.generate_picture_images = True
    opts.force_backend_text = False

    # tables
    opts.do_table_structure = CFG.enable_tables
    tso = opts.table_structure_options
    tso.mode = TableFormerMode.ACCURATE
    tso.do_cell_matching = CFG.enable_cell_matching

    # language reconciliation
    easy_codes = {c for c in CFG.ocr_languages}
    tess_codes = {LANG_MAP_EASY2TESS.get(c, c) for c in easy_codes} | {"eng"}  # ensure eng
    easy_codes = {LANG_MAP_TESS2EASY.get(c, c) for c in tess_codes}

    opts.do_ocr = CFG.enable_ocr
    opts.ocr_options = EasyOcrOptions(
        lang=list(easy_codes),
        force_full_page_ocr=CFG.force_full_page_ocr,
        confidence_threshold=0.30,
    )

    opts.accelerator_options = AcceleratorOptions(device=AcceleratorDevice.AUTO, num_threads=8)
    return opts


@lru_cache(maxsize=2)
def _conv():
    from docling.backend.docling_parse_v2_backend import DoclingParseV2DocumentBackend
    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import DocumentConverter, FormatOption
    from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

    return DocumentConverter(
        format_options={
            InputFormat.PDF: FormatOption(
                pipeline_cls=StandardPdfPipeline,
                pipeline_options=_build_opts(),
                backend=DoclingParseV2DocumentBackend,
            )
        }
    )


# ── helpers ───────────────────────────────────────────────────────────────
_CLEAN_CACHE: Dict[str, str] = {}


def _clean(t: str) -> str:
    if t in _CLEAN_CACHE:
        return _CLEAN_CACHE[t]
    cleaned = " ".join(t.split()) if t else t
    _CLEAN_CACHE[t] = cleaned
    return cleaned


def _in_margin(b: Dict[str, float], w: float, h: float, pct: float) -> bool:
    if not all(k in b for k in ("x0", "y0", "x1", "y1")):
        return False
    mx, my = pct * w, pct * h
    return b["x0"] < mx or b["x1"] > w - mx or b["y0"] < my or b["y1"] > h - my


# ── main extractor ────────────────────────────────────────────────────────
class TradePDFExtractor:
    def __init__(
        self,
        num_threads: Optional[int] = None,
        debug_dir: Optional[Path] = None,
        meta_lookup: Optional[Dict[str, Any]] = None,
    ):
        if num_threads:
            os.environ.setdefault("OMP_NUM_THREADS", str(num_threads))
        self.debug_dir = debug_dir
        self.meta_lookup = meta_lookup or {}
        self._conv = _conv()

    # -------- public I/O helpers ---------------------------------------
    def from_path(self, path: str | Path) -> DocumentParseResult:
        with open(path, "rb") as f:
            return self.from_bytes(f.read(), name=Path(path).name)

    async def from_url(self, url: str) -> DocumentParseResult:
        if not HAS_AIOHTTP:
            return DocumentParseResult(False, error_message="aiohttp missing")
        tout = aiohttp.ClientTimeout(total=CFG.timeout_seconds)
        async with aiohttp.ClientSession(timeout=tout) as s:
            async with s.get(url) as r:
                r.raise_for_status()
                blob = await r.read()
        return self.from_bytes(blob, name=url.rsplit("/", 1)[-1])

    def from_bytes(self, blob: bytes, *, name: str = "upload.pdf") -> DocumentParseResult:
        from docling.document_converter import ConversionStatus
        from docling_core.types.io import DocumentStream

        try:
            conv = self._conv.convert(DocumentStream(name=name, stream=io.BytesIO(blob)))
            if conv.status != ConversionStatus.SUCCESS:
                return DocumentParseResult(False, error_message=str(conv.status))
            raw = conv.document.export_to_dict()
            if self.debug_dir:
                self._dump_raw(raw)
            return DocumentParseResult(True, **self._post(raw, blob))
        except Exception as e:
            return DocumentParseResult(False, error_message=str(e))

    # ------------------------------------------------------------------ #
    #  post processing                                                   #
    # ------------------------------------------------------------------ #
    def _post(self, doc: Dict[str, Any], blob: bytes) -> Dict[str, Any]:
        meta = {
            "filename": doc.get("origin", {}).get("filename", ""),
            "pages_count": len(doc.get("pages", [])),
            "tables_count": len(doc.get("tables", [])),
            "extraction_method": "docling+tesseract_v2",
        }
        meta.update(self.meta_lookup.get(meta["filename"].rsplit(".", 1)[0], {}))

        dims = {
            p["page_no"]: (p.get("width", 1), p.get("height", 1))
            for p in doc.get("pages", [])
            if isinstance(p, dict)
        }

        # -------- vector text ------------------------------------------
        txt_blocks: List[Any] = []
        conf_map: Dict[str, Any] = {}
        for blk in doc.get("texts", []):
            if blk.get("label") in {"page_header", "page_footer", "page_number"}:
                continue
            prov = blk.get("prov", [{}])[0]
            bbox, page = prov.get("bbox", {}), prov.get("page_no", 1)
            if bbox and _in_margin(bbox, *dims.get(page, (1, 1)), pct=0.02):
                continue
            t = _clean(blk.get("text", ""))
            if t:
                txt_blocks.append({**blk, "text": t})
                conf_map.setdefault(page, []).append(float(blk.get("conf", 1.0)))

        self._class = self._classify(self._group(txt_blocks, []))

        noisy_pages = self._detect_noisy_pages(txt_blocks)
        if noisy_pages:
            txt_blocks.extend(self._ocr_pages(blob, noisy_pages, dims))
            for b in txt_blocks:
                if b["label"] in {"tesseract", "easyocr"}:
                    p = b["prov"][0]["page_no"]
                    conf_map.setdefault(p, []).append(b["conf"])

        for tbl in doc.get("tables", []):
            p = tbl.get("prov", [{}])[0].get("page_no", 1)
            for row in tbl.get("data", {}).get("grid", []):
                for c in row:
                    conf_map.setdefault(p, []).append(float(c.get("conf", 1.0)))

        meta["page_confidence"] = {p: round(statistics.mean(v), 4) for p, v in conf_map.items()}

        text_content = "\n\n".join(b["text"] for b in txt_blocks)
        tables = self._tables(doc.get("tables", []), txt_blocks)
        pages = self._group(txt_blocks, doc.get("tables", []))
        meta.update(
            {
                "doc_type": self._class,
                "text_blocks_count": len(txt_blocks),
                "ready_for_llm": all(t["rows"] <= 120 for t in tables),
            }
        )

        return {
            "text_content": text_content,
            "tables": tables,
            "metadata": meta,
            "page_content": pages,
        }

    # ------------------------------------------------------------------ #
    #  OCR helpers                                                       #
    # ------------------------------------------------------------------ #
    def _detect_noisy_pages(self, blocks):
        noisy, by_page = [], {}
        for b in blocks:
            by_page.setdefault(b["prov"][0]["page_no"], []).append(b["text"])
        for p, lines in by_page.items():
            joined = " ".join(lines)
            if not joined:
                continue
            short = sum(1 for w in joined.split() if len(w) <= 4 and w.isupper())
            if short / max(len(joined.split()), 1) > 0.30:
                noisy.append(p)
        return noisy

    def _convert_pdf_pages_to_images(
        self, blob: bytes, pages: List[int], dpi: int = 300
    ) -> List[tuple]:
        """Render the given (1-based) PDF pages to PIL Images via PyMuPDF.

        Raises ImportError if PyMuPDF is unavailable.
        """
        if not HAS_PYMUPDF:
            raise ImportError(
                "PyMuPDF (fitz) is required for PDF to image conversion. "
                "Install with: pip install PyMuPDF"
            )

        try:
            # Open PDF document from bytes
            doc = fitz.open(stream=blob, filetype="pdf")
        except Exception as e:
            raise Exception(f"Failed to open PDF document: {e}")

        images = []

        try:
            for page_num in pages:
                # PyMuPDF uses 0-based indexing
                page_index = page_num - 1
                if page_index >= doc.page_count or page_index < 0:
                    continue

                try:
                    page = doc[page_index]

                    # Create transformation matrix for DPI scaling
                    # PyMuPDF default is 72 DPI, so we scale accordingly
                    scale = dpi / 72.0
                    mat = fitz.Matrix(scale, scale)

                    # Render page to pixmap
                    pix = page.get_pixmap(matrix=mat)

                    # Convert pixmap to PIL Image
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))

                    images.append((page_num, img))

                except Exception as e:
                    logger.warning(f"Failed to convert page {page_num} to image: {e}")
                    continue

        finally:
            doc.close()

        return images

    def _ocr_pages(self, blob: bytes, pages: List[int], dims) -> List[Dict[str, Any]]:
        lang_map = {
            "invoice": ["eng", "chi_sim"],
            "packing_list": ["eng", "chi_sim"],
            "bol": ["eng"],
            "coo": ["eng", "chi_sim", "ara"],
        }
        langs = lang_map.get(self._class, ["eng", "chi_sim", "ara", "kor", "spa", "fra"])
        lang_arg = "+".join(langs)

        # Use PyMuPDF instead of pdf2image
        try:
            images = self._convert_pdf_pages_to_images(blob, pages, dpi=300)
        except ImportError as e:
            # PyMuPDF not available, cannot perform OCR
            logger.error(f"PyMuPDF not available for PDF to image conversion: {e}")
            return []
        except Exception as e:
            # Other errors during image conversion
            logger.warning(f"PDF to image conversion failed: {e}")
            return []

        blocks = []
        for pn, img in images:
            tess = pytesseract.image_to_data(
                img, lang=lang_arg, output_type=pytesseract.Output.DICT
            )
            words = [t for t in tess["text"] if t.strip()]
            if len(words) < 10 and HAS_EASYOCR:
                blocks.extend(self._easyocr(img, pn, langs))
                continue
            for i, txt in enumerate(tess["text"]):
                clean = _clean(txt)
                if not clean:
                    continue
                x, y, w, h = (tess["left"][i], tess["top"][i], tess["width"][i], tess["height"][i])
                blocks.append(
                    {
                        "text": clean,
                        "conf": float(tess["conf"][i] or "0") / 100,
                        "label": "tesseract",
                        "prov": [
                            {"page_no": pn, "bbox": {"x0": x, "y0": y, "x1": x + w, "y1": y + h}}
                        ],
                    }
                )
        return blocks

    def _easyocr(self, img: Image.Image, pn: int, tess_langs) -> List[Dict[str, Any]]:
        if not HAS_EASYOCR:
            return []
        easy_langs = [LANG_MAP_TESS2EASY.get(c, c) for c in tess_langs]
        reader = Reader(easy_langs)
        out = []
        for txt, conf, (x0, y0, x1, y1) in reader.readtext(img, detail=1):
            out.append(
                {
                    "text": _clean(txt),
                    "conf": float(conf),
                    "label": "easyocr",
                    "prov": [{"page_no": pn, "bbox": {"x0": x0, "y0": y0, "x1": x1, "y1": y1}}],
                }
            )
        return out

    # ------------------------------------------------------------------ #
    #  table / grouping helpers                                          #
    # ------------------------------------------------------------------ #
    def _tables(self, tbl_json, txt_blocks):
        from tabulate import tabulate

        txt_by_page, out = {}, []
        for b in txt_blocks:
            txt_by_page.setdefault(b["prov"][0]["page_no"], []).append(b["text"])
        for idx, t in enumerate(tbl_json):
            grid = [
                [_clean(c.get("text", "")) for c in r] for r in t.get("data", {}).get("grid", [])
            ]
            if (
                len(grid) <= 2
                and grid
                and any("hscode" in h.lower().replace(" ", "") for h in grid[0])
            ):
                grid = self._rebuild_coo(grid, txt_by_page.get(t["prov"][0]["page_no"], []))
            md = (
                tabulate(grid[1:], headers=grid[0], tablefmt="github", disable_numparse=True)
                if grid
                else ""
            )
            prov = t.get("prov", [{}])[0]
            out.append(
                {
                    "table_id": idx,
                    "page": prov.get("page_no", 1),
                    "rows": len(grid),
                    "cols": len(grid[0]) if grid else 0,
                    "data": grid,
                    "markdown": md,
                }
            )
        return out

    def _rebuild_coo(self, grid, lines):
        if not lines or len(grid) != 2:
            return grid
        header, buckets = grid[0], [[] for _ in range(5)]
        for ln in lines:
            parts = ln.split(" ", 4) + [""]
            for i, seg in enumerate(parts[:5]):
                buckets[i].append(seg)
        rows = list(zip(*buckets))
        return [header] + [list(r) for r in rows if any(r)]

    def _group(self, txt, tbl):
        pages = {}
        for b in txt:
            p = b["prov"][0]["page_no"]
            pages.setdefault(p, {"texts": [], "tables": []})
            pages[p]["texts"].append({"text": b["text"], "type": b.get("label", "text")})
        for i, t in enumerate(tbl):
            p = t["prov"][0]["page_no"]
            pages.setdefault(p, {"texts": [], "tables": []})
            pages[p]["tables"].append({"table_id": i})
        return [{"page": p, "content": c} for p, c in sorted(pages.items())]

    # ------------------------------------------------------------------ #
    #  classification / misc                                             #
    # ------------------------------------------------------------------ #
    def _classify(self, pages):
        keys = {
            "invoice": ["COMMERCIAL INVOICE"],
            "packing_list": ["PACKING LIST"],
            "bol": ["BILL OF LADING", "B/L"],
            "coo": ["CERTIFICATE OF ORIGIN"],
        }
        for pg in pages[:3]:
            for blk in pg["content"]["texts"]:
                up = blk["text"].upper()
                for k, kw in keys.items():
                    if any(w in up for w in kw):
                        return k
        return "unknown"

    def _dump_raw(self, raw):
        if self.debug_dir is None:
            return
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        fn = raw.get("origin", {}).get("filename", "doc")
        with (self.debug_dir / f"{fn}.raw.json").open("w", encoding="utf-8") as fp:
            json.dump(raw, fp, indent=2, ensure_ascii=False)
