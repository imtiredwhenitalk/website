"""AI helpers: optional OpenAI client and OCR file reading utilities.

This module provides a small `AI` wrapper that can:
- initialize an OpenAI client (if `OPENAI_API_KEY` and `openai` lib are available)
- extract text from images and PDFs using local `pytesseract`/`pdf2image`
  or by sending files to an external OCR API set via `OCR_API_URL` env var.

Usage examples:
    ai = AI()
    text = ai.detect_and_read('documents/scan.jpg')

The implementation is defensive: if local OCR libs are missing it will
attempt to use an external OCR endpoint (multipart POST) if `OCR_API_URL`
is set in the environment.
"""

from __future__ import annotations

import io
import logging
import mimetypes
import os
from typing import Optional

import hashlib
import json
import pathlib
import subprocess
import time

logger = logging.getLogger(__name__)

try:
    import openai
except Exception:
    openai = None

try:
    import requests
except Exception:
    requests = None

try:
    from PIL import Image
    import pytesseract
except Exception:
    Image = None
    pytesseract = None

try:
    from pdf2image import convert_from_path
except Exception:
    convert_from_path = None


class AI:
    def __init__(self, *, ocr_api_url: Optional[str] = None, openai_api_key: Optional[str] = None):
        """Create AI helper.

        - `ocr_api_url`: optional URL to a local OCR service that accepts multipart
          uploads and returns plain text (or JSON with `text` key).
        - `openai_api_key`: explicit OpenAI API key; falls back to `OPENAI_API_KEY` env var.
        """
        self.ocr_api_url = ocr_api_url or os.getenv("OCR_API_URL")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.openai = None
        if openai and self.openai_api_key:
            try:
                openai.api_key = self.openai_api_key
                self.openai = openai
            except Exception:
                logger.exception("Failed to initialize OpenAI client")
        # cache directory for OCR results and metadata
        self.cache_dir = pathlib.Path(os.getenv("AI_CACHE_DIR", os.path.join(os.getcwd(), ".cache", "ai")))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._branches_cache_file = self.cache_dir / "branches.json"

    # ---------- OCR via local libs ----------
    def _ocr_image_local(self, image_bytes: bytes) -> str:
        if Image is None or pytesseract is None:
            raise RuntimeError("Local OCR not available: install pillow and pytesseract or set OCR_API_URL")
        img = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(img)
        return text

    def _ocr_pdf_local(self, pdf_path: str) -> str:
        if convert_from_path is None or pytesseract is None or Image is None:
            raise RuntimeError("Local PDF OCR not available: install pdf2image, pillow and pytesseract or set OCR_API_URL")
        text_parts = []
        pages = convert_from_path(pdf_path)
        for page in pages:
            text_parts.append(pytesseract.image_to_string(page))
        return "\n\n".join(text_parts)

    # ---------- OCR via external API ----------
    def _send_to_ocr_api(self, file_path: Optional[str], file_bytes: Optional[bytes], filename: str) -> str:
        if not self.ocr_api_url:
            raise RuntimeError("OCR API URL not configured (OCR_API_URL)")
        if requests is None:
            raise RuntimeError("`requests` library is required to call external OCR API")
        files = {}
        if file_bytes is not None:
            files["file"] = (filename, io.BytesIO(file_bytes))
        else:
            files["file"] = (filename, open(file_path, "rb"))
        try:
            resp = requests.post(self.ocr_api_url, files=files, timeout=60)
        finally:
            if file_bytes is None:
                files["file"][1].close()
        resp.raise_for_status()
        # try json 'text' key first, otherwise return raw text
        try:
            data = resp.json()
            if isinstance(data, dict) and "text" in data:
                return data["text"]
            # if API returned other structure, try common keys
            for key in ("result", "ocr_text", "data"):
                if key in data:
                    return data[key]
            # fallback to raw stringified json
            return str(data)
        except ValueError:
            return resp.text

    # ----------------- Caching helpers -----------------
    def _cache_get(self, key: str) -> Optional[str]:
        path = self.cache_dir / f"{key}.txt"
        if path.exists():
            try:
                return path.read_text(encoding="utf-8")
            except Exception:
                return None
        return None

    def _cache_set(self, key: str, text: str) -> None:
        path = self.cache_dir / f"{key}.txt"
        path.write_text(text, encoding="utf-8")

    def _file_hash_key(self, path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    # ----------------- Git branches discovery -----------------
    def get_git_branches(self, repo_path: str = ".", force: bool = False, cache_ttl: int = 300) -> list:
        """Return list of branches (local and remote). Results cached to disk for `cache_ttl` seconds."""
        # use cached file if fresh
        if self._branches_cache_file.exists() and not force:
            try:
                stat = self._branches_cache_file.stat()
                if (time.time() - stat.st_mtime) < cache_ttl:
                    data = json.loads(self._branches_cache_file.read_text())
                    return data.get("branches", [])
            except Exception:
                pass
        # run git command
        try:
            out = subprocess.check_output(["git", "branch", "-a"], cwd=repo_path, text=True, stderr=subprocess.STDOUT)
            branches = [line.strip().lstrip("*").strip() for line in out.splitlines() if line.strip()]
        except Exception:
            branches = []
        try:
            self._branches_cache_file.write_text(json.dumps({"branches": branches, "fetched_at": time.time()}))
        except Exception:
            pass
        return branches

    # ---------- Public helpers ----------
    def read_image(self, path: str) -> str:
        """Read text from an image file (JPEG/PNG/etc.)."""
        key = self._file_hash_key(path)
        cached = self._cache_get(key)
        if cached is not None:
            return cached
        with open(path, "rb") as f:
            b = f.read()
        # prefer local OCR
        try:
            text = self._ocr_image_local(b)
        except Exception:
            logger.debug("Local OCR failed or unavailable, trying OCR API", exc_info=True)
            text = self._send_to_ocr_api(path, b, os.path.basename(path))
        # save to cache
        try:
            self._cache_set(key, text)
        except Exception:
            logger.exception("Failed to write OCR cache")
        return text

    def read_pdf(self, path: str) -> str:
        """Extract text from a PDF file using local OCR or external service."""
        # prefer local conversion
        key = self._file_hash_key(path)
        cached = self._cache_get(key)
        if cached is not None:
            return cached
        try:
            text = self._ocr_pdf_local(path)
        except Exception:
            logger.debug("Local PDF OCR failed or unavailable, trying OCR API", exc_info=True)
            with open(path, "rb") as f:
                b = f.read()
            text = self._send_to_ocr_api(path, b, os.path.basename(path))
        try:
            self._cache_set(key, text)
        except Exception:
            logger.exception("Failed to write OCR cache")
        return text

    def detect_and_read(self, path: str) -> str:
        """Detect file type by mimetype/extension and extract text accordingly."""
        mtype, _ = mimetypes.guess_type(path)
        if mtype == "application/pdf" or path.lower().endswith(".pdf"):
            return self.read_pdf(path)
        else:
            return self.read_image(path)


__all__ = ["AI"]