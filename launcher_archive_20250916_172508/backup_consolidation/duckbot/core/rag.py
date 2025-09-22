import os
import re
import json
import sqlite3
import time
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import requests
from bs4 import BeautifulSoup

from .settings_gpt import load_settings


# Simple, dependency-free RAG with SQLite TF-IDF index
# - Ingests plaintext/markdown files into chunks
# - Builds postings (term -> chunk tf) and term df
# - Retrieves with TF-IDF cosine approximation (unnormalized score)

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "rag_index.db"

SUPPORTED_EXTENSIONS = {
    ".md", ".markdown", ".txt", ".log",
    ".py", ".html", ".htm", ".json"
}

STOPWORDS = set("""
the a an and or but if on in at for of to by with from up down over under above below into out about against between among
is are was were be been being do does did doing have has had having can could should would may might must will shall not no
this that these those there here it its it's i you he she we they them our your their my mine ours yours theirs as than then
""".split())


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def ensure_db():
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY,
            source TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            created_at REAL NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS terms (
            term TEXT PRIMARY KEY,
            df INTEGER NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS postings (
            term TEXT NOT NULL,
            chunk_id INTEGER NOT NULL,
            tf INTEGER NOT NULL,
            PRIMARY KEY (term, chunk_id)
        )
        """
    )
    conn.commit()
    conn.close()


def _tokenize(text: str) -> List[str]:
    words = re.findall(r"[A-Za-z0-9_]{2,}", text.lower())
    return [w for w in words if w not in STOPWORDS]


def _chunk_text(text: str, max_chars: int = 800, overlap: int = 120) -> List[str]:
    text = text.strip()
    if not text:
        return []
    chunks = []
    i = 0
    n = len(text)
    while i < n:
        j = min(n, i + max_chars)
        chunk = text[i:j]
        chunks.append(chunk)
        if j == n:
            break
        i = max(i + max_chars - overlap, i + 1)
    return chunks


def _read_text_file(p: Path) -> Optional[str]:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None


def _list_candidate_files(root: Path) -> List[Path]:
    files: List[Path] = []
    if root.is_file():
        if root.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(root)
        return files
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(root.rglob(f"*{ext}"))
    return files


def clear_index():
    ensure_db()
    conn = _connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM postings;")
    cur.execute("DELETE FROM terms;")
    cur.execute("DELETE FROM chunks;")
    conn.commit()
    conn.close()


def ingest_paths(paths: List[str], max_chars: int = 800, overlap: int = 120) -> Dict:
    ensure_db()
    conn = _connect()
    cur = conn.cursor()
    added_chunks = 0
    added_terms = 0
    start = time.time()

    for path_str in paths:
        root = Path(path_str).resolve()
        for p in _list_candidate_files(root):
            text = _read_text_file(p)
            if not text:
                continue
            # Lightweight cleaning for code/markdown
            chunks = _chunk_text(text, max_chars=max_chars, overlap=overlap)
            for idx, chunk in enumerate(chunks):
                cur.execute(
                    "INSERT INTO chunks(source, chunk_index, text, created_at) VALUES(?,?,?,?)",
                    (str(p), idx, chunk, time.time()),
                )
                chunk_id = cur.lastrowid
                added_chunks += 1
                # Term frequencies for chunk
                tf: Dict[str, int] = {}
                for tok in _tokenize(chunk):
                    tf[tok] = tf.get(tok, 0) + 1
                for term, freq in tf.items():
                    cur.execute(
                        "INSERT OR IGNORE INTO terms(term, df) VALUES(?, 0)", (term,)
                    )
                    cur.execute(
                        "UPDATE terms SET df = df + 1 WHERE term = ?", (term,)
                    )
                    cur.execute(
                        "INSERT OR REPLACE INTO postings(term, chunk_id, tf) VALUES(?,?,?)",
                        (term, chunk_id, freq),
                    )
                    added_terms += 1

    conn.commit()
    conn.close()
    return {
        "ok": True,
        "chunks_added": added_chunks,
        "postings_added": added_terms,
        "elapsed_sec": round(time.time() - start, 3),
    }

def add_document(file_path: str):
    """Add a single document to the RAG index."""
    ingest_paths([file_path])

def add_website(url: str):
    """Add a website to the RAG index."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        if text:
            # Create a temporary file to ingest
            temp_dir = BASE_DIR / "temp"
            temp_dir.mkdir(exist_ok=True)
            temp_file = temp_dir / f"{hashlib.md5(url.encode()).hexdigest()}.txt"
            temp_file.write_text(text, encoding='utf-8')
            ingest_paths([str(temp_file)])
    except Exception as e:
        print(f"Error crawling website: {e}")


def index_stats() -> Dict:
    ensure_db()
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM chunks")
    chunks = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM terms")
    terms = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM postings")
    posts = cur.fetchone()[0]
    conn.close()
    return {"chunks": chunks, "terms": terms, "postings": posts, "db_path": str(DB_PATH)}


def retrieve(query: str, top_k: int = 4) -> List[Tuple[int, float, str, str]]:
    """Return list of (chunk_id, score, source, text) sorted by score desc"""
    ensure_db()
    tokens = _tokenize(query)
    if not tokens:
        return []
    conn = _connect()
    cur = conn.cursor()
    # Fetch DF for tokens
    df: Dict[str, int] = {}
    for t in set(tokens):
        cur.execute("SELECT df FROM terms WHERE term=?", (t,))
        row = cur.fetchone()
        if row:
            df[t] = row[0]
    if not df:
        conn.close()
        return []
    # Compute IDF (log scaling) using total docs = chunk count
    cur.execute("SELECT COUNT(*) FROM chunks")
    N = max(1, cur.fetchone()[0])
    idf: Dict[str, float] = {}
    import math
    for t, dfi in df.items():
        idf[t] = math.log((N + 1) / (dfi + 1)) + 1.0
    # Aggregate scores across postings
    scores: Dict[int, float] = {}
    for t in df.keys():
        cur.execute("SELECT chunk_id, tf FROM postings WHERE term=?", (t,))
        for chunk_id, tf in cur.fetchall():
            scores[chunk_id] = scores.get(chunk_id, 0.0) + tf * idf[t]
    if not scores:
        conn.close()
        return []
    # Take top_k
    best = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    results: List[Tuple[int, float, str, str]] = []
    for chunk_id, score in best:
        cur.execute("SELECT source, text FROM chunks WHERE id=?", (chunk_id,))
        row = cur.fetchone()
        if row:
            results.append((chunk_id, score, row[0], row[1]))
    conn.close()
    return results


def build_context(query: str, top_k: int = 4, max_chars: int = 2000) -> Tuple[str, List[Dict]]:
    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        return "", []
    context_parts: List[str] = []
    meta: List[Dict] = []
    total = 0
    for (cid, score, source, text) in chunks:
        piece = f"[Source: {Path(source).name} | Score: {round(score,2)}]\n{text.strip()}\n"
        if total + len(piece) > max_chars:
            break
        context_parts.append(piece)
        total += len(piece)
        meta.append({"chunk_id": cid, "score": score, "source": source})
    return "\n\n".join(context_parts), meta


def rag_enabled() -> bool:
    s = load_settings()
    return str(s.get("RAG_ENABLED", "1")).strip() not in {"0", "false", "no"}


def maybe_augment_with_rag(task: Dict) -> Tuple[Dict, Dict]:
    """If enabled, augment task['prompt'] with retrieved context.
    Returns (task_or_augmented, rag_info)
    """
    try:
        if not rag_enabled():
            return task, {"used": False}
        s = load_settings()
        include_kinds = (s.get("RAG_INCLUDE_KINDS") or "status,summary,code,json_format,long_form,*,reasoning").split(",")
        include_kinds = [k.strip() for k in include_kinds if k.strip()]
        kind = (task.get("kind") or "*").strip()
        override = (task.get("override") or "").lower()
        if "no_rag" in override:
            return task, {"used": False, "reason": "override:no_rag"}
        if include_kinds != ["*"] and kind not in include_kinds and "*" not in include_kinds:
            return task, {"used": False, "reason": f"kind_excluded:{kind}"}

        top_k = int(s.get("RAG_TOP_K", 4))
        max_chars = int(s.get("RAG_MAX_CONTEXT_CHARS", 2000))
        query = (task.get("prompt") or "").strip()
        if not query:
            return task, {"used": False, "reason": "empty_prompt"}
        context, meta = build_context(query, top_k=top_k, max_chars=max_chars)
        if not context:
            return task, {"used": False, "reason": "no_matches"}

        augmented_prompt = (
            "You are DuckBot with Retrieval-Augmented Generation. Use the context to answer."
            "If context conflicts with prior assumptions, trust the context."
            "\n[CONTEXT]\n" + context + "\n[END CONTEXT]\n\n"
            "[USER PROMPT]\n" + query
        )
        new_task = dict(task)
        new_task["prompt"] = augmented_prompt
        return new_task, {"used": True, "chunks": meta}
    except Exception as e:
        return task, {"used": False, "error": str(e)}


def auto_ingest_defaults() -> Dict:
    """Best-effort ingestion of local docs on first call."""
    s = load_settings()
    sources = []
    # Prioritize project docs
    repo_root = Path(__file__).parent.parent
    for name in [
        "README.md", "AGENTS.md", "AI-Information.md", "FINAL_IMPROVEMENTS_SUMMARY.md",
        "FIXES_CHANGELOG.md", "QUICKSTART.md", "QWEN.md"
    ]:
        p = repo_root / name
        if p.exists():
            sources.append(str(p))
    # Assets/docs dir
    candidate = repo_root / "assets"
    if candidate.exists():
        sources.append(str(candidate))
    # Duckbot templates & core python for domain knowledge (shallow)
    sources.append(str(repo_root / "duckbot" / "templates"))
    # Avoid massive code ingestion by default; users can add more paths via API
    if not sources:
        sources.append(str(repo_root))
    return ingest_paths(sources)