"""Google ADK research assistant using OpenAlex structured scholarly metadata.

Place as research_assistant/agent.py, alongside research_assistant/.env.
Run `adk web` from the directory containing research_assistant/.
"""

import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from google.adk.agents import Agent

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")
load_dotenv(BASE_DIR / ".env", override=False)

if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("Set GOOGLE_API_KEY in research_assistant/.env")

MODEL = os.getenv("ADK_MODEL", "gemini-2.5-flash-lite")
OPENALEX_API_KEY = os.getenv("OPENALEX_API_KEY", "").strip()
OPENALEX_EMAIL = os.getenv("OPENALEX_EMAIL", "").strip()
MODEL_DELAY = max(0.0, float(os.getenv("MODEL_MIN_INTERVAL_SECONDS", "4")))
API_DELAY = max(0.0, float(os.getenv("OPENALEX_MIN_INTERVAL_SECONDS", "3")))
MAX_RESULTS = max(1, min(20, int(os.getenv("MAX_SEARCH_RESULTS", "6"))))
TIMEOUT = max(5, min(60, int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))))

session = requests.Session()
session.headers.update({"User-Agent": "ADKResearchAssistant/1.0 (academic literature research)", "Accept": "application/json"})
model_lock = threading.Lock()
api_lock = threading.Lock()
last_model = 0.0
last_api = 0.0


def rate_limit_before_model(callback_context, llm_request):
    """Minimum gap between model requests within this Python process."""
    global last_model
    with model_lock:
        remaining = MODEL_DELAY - (time.monotonic() - last_model)
        if remaining > 0:
            time.sleep(remaining)
        last_model = time.monotonic()
    return None


def _openalex_get(endpoint: str, params: dict = None) -> dict:
    """One throttled request; fail explicitly rather than silently returning empty papers."""
    global last_api
    with api_lock:
        remaining = API_DELAY - (time.monotonic() - last_api)
        if remaining > 0:
            time.sleep(remaining)
        last_api = time.monotonic()
        query = dict(params or {})
        if OPENALEX_API_KEY:
            query["api_key"] = OPENALEX_API_KEY
        if OPENALEX_EMAIL:
            query["mailto"] = OPENALEX_EMAIL
        response = session.get(
            "https://api.openalex.org/" + endpoint.lstrip("/"),
            params=query, timeout=TIMEOUT,
        )
    if response.status_code in (401, 403):
        raise RuntimeError(
            f"OpenAlex HTTP {response.status_code}: access denied. "
            "Check OPENALEX_API_KEY and the current OpenAlex access requirements."
        )
    if response.status_code == 429:
        raise RuntimeError("OpenAlex HTTP 429: rate limit reached; wait or review API quota.")
    response.raise_for_status()
    return response.json()


def _abstract(inverted_index: Any) -> str:
    """Restore word order from OpenAlex abstract_inverted_index."""
    if not isinstance(inverted_index, dict) or not inverted_index:
        return ""
    positions = []
    for word, offsets in inverted_index.items():
        for offset in offsets:
            if isinstance(offset, int) and 0 <= offset < 100000:
                positions.append((offset, word))
    positions.sort(key=lambda x: x[0])
    return " ".join(word for _, word in positions)


def _doi(value: Any) -> str:
    if not value:
        return ""
    value = str(value).strip()
    if value.lower().startswith("https://doi.org/"):
        return value
    return "https://doi.org/" + value.removeprefix("doi:")


def _record(work: dict) -> dict:
    primary = work.get("primary_location") or {}
    source = primary.get("source") or {}
    authors = [
        a.get("author", {}).get("display_name", "")
        for a in (work.get("authorships") or [])
        if a.get("author", {}).get("display_name")
    ]
    abstract = _abstract(work.get("abstract_inverted_index"))
    return {
        "openalex_id": work.get("id"),
        "title": work.get("display_name") or work.get("title"),
        "authors": authors,
        "year": work.get("publication_year"),
        "publication_date": work.get("publication_date"),
        "journal_or_venue": source.get("display_name"),
        "volume": (work.get("biblio") or {}).get("volume"),
        "issue": (work.get("biblio") or {}).get("issue"),
        "first_page": (work.get("biblio") or {}).get("first_page"),
        "last_page": (work.get("biblio") or {}).get("last_page"),
        "doi": _doi(work.get("doi")),
        "paper_url": primary.get("landing_page_url") or work.get("doi") or work.get("id"),
        "open_access_url": (work.get("best_oa_location") or {}).get("pdf_url"),
        "type": work.get("type"),
        "cited_by_count": work.get("cited_by_count"),
        "abstract": abstract or None,
        "abstract_status": "available" if abstract else "not_available_in_openalex",
        "source": "OpenAlex API",
    }


def search_research_papers(query: str, max_results: int = 5, start_year: int = 2020, end_year: int = 2026) -> Dict[str, Any]:
    """Search OpenAlex works by keywords and publication-year range."""
    if not query.strip():
        return {"status": "error", "message": "Query cannot be empty."}
    if start_year > end_year:
        return {"status": "error", "message": "start_year must not exceed end_year."}
    try:
        data = _openalex_get("works", {
            "search": query.strip(),
            "filter": f"from_publication_date:{start_year}-01-01,to_publication_date:{end_year}-12-31",
            "per-page": max(1, min(max_results, MAX_RESULTS)),
        })
        papers = [_record(work) for work in data.get("results", [])]
        return {
            "status": "success" if papers else "no_results",
            "query": query,
            "total_matches": (data.get("meta") or {}).get("count"),
            "count": len(papers),
            "papers": papers,
            "note": "OpenAlex records are metadata; abstracts and full text may be unavailable.",
        }
    except Exception as exc:
        return {"status": "error", "query": query, "message": str(exc), "papers": []}


def retrieve_paper_abstracts(openalex_ids: List[str]) -> Dict[str, Any]:
    """Retrieve full OpenAlex metadata and available reconstructed abstracts by work IDs."""
    records = []
    for identifier in openalex_ids[:MAX_RESULTS]:
        work_id = str(identifier).strip().rstrip("/").split("/")[-1]
        if not re.fullmatch(r"W\d+", work_id):
            records.append({"id": identifier, "status": "invalid_id"})
            continue
        try:
            work = _openalex_get("works/" + quote(work_id, safe=""))
            records.append({"status": "retrieved", **_record(work)})
        except Exception as exc:
            records.append({"id": identifier, "status": "error", "message": str(exc)})
    return {"status": "completed", "papers": records}


def verify_paper_sources(openalex_ids: List[str]) -> Dict[str, Any]:
    """Recheck identifiers against OpenAlex records and report DOI/venue metadata availability.

    OpenAlex record existence is not independent publisher or peer-review verification.
    """
    checks = []
    for identifier in openalex_ids[:MAX_RESULTS]:
        work_id = str(identifier).strip().rstrip("/").split("/")[-1]
        if not re.fullmatch(r"W\d+", work_id):
            checks.append({"id": identifier, "status": "invalid_id"})
            continue
        try:
            work = _openalex_get("works/" + quote(work_id, safe=""))
            paper = _record(work)
            checks.append({
                "openalex_id": paper["openalex_id"],
                "title": paper["title"],
                "doi": paper["doi"] or None,
                "venue": paper["journal_or_venue"],
                "source_url": paper["paper_url"],
                "status": "openalex_record_confirmed",
                "independently_publisher_verified": False,
                "note": "Metadata confirmed in OpenAlex only; publisher and peer-review status not independently verified.",
            })
        except Exception as exc:
            checks.append({"id": identifier, "status": "verification_failed", "message": str(exc)})
    return {"status": "completed", "checks": checks}


def _apa_author_name(full_name: str) -> str:
    """Convert a display name into an APA-style surname and initials.

    Handles common 'Given Middle Family' and 'Family, Given Middle' forms.
    Name parsing is inherently ambiguous for some cultures and compound surnames;
    the result should be checked against the publisher's author list.
    """
    name = re.sub(r"\s+", " ", (full_name or "").strip())
    if not name:
        return ""

    if "," in name:
        family, given = [part.strip() for part in name.split(",", 1)]
        given_parts = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ'-]*", given)
        initials = " ".join(f"{part[0].upper()}." for part in given_parts)
        return f"{family}, {initials}".strip().rstrip(",")

    parts = name.split()
    if len(parts) == 1:
        return parts[0]

    # Treat the final token as the family name; preserve preceding tokens as initials.
    # This is a best-effort transformation of OpenAlex display_name values.
    family = parts[-1]
    given_parts = parts[:-1]
    initials = " ".join(f"{part[0].upper()}." for part in given_parts if part)
    return f"{family}, {initials}"


def _apa_authors(authors: list) -> str:
    """Format APA 7 author list, including the 20-author truncation rule."""
    cleaned = [str(a).strip() for a in authors if str(a).strip()]
    formatted = [_apa_author_name(a) for a in cleaned]
    formatted = [a for a in formatted if a]

    if not formatted:
        return ""

    if len(formatted) <= 20:
        if len(formatted) == 1:
            return formatted[0]
        if len(formatted) == 2:
            return f"{formatted[0]}, & {formatted[1]}"
        return ", ".join(formatted[:-1]) + f", & {formatted[-1]}"

    # APA 7: first 19 authors, ellipsis, then final author.
    return ", ".join(formatted[:19]) + ", . . . " + formatted[-1]


def _apa_year(paper: dict) -> str:
    year = paper.get("year")
    if not year:
        publication_date = str(paper.get("publication_date") or "")
        match = re.search(r"\b(?:19|20)\d{2}\b", publication_date)
        year = match.group(0) if match else None
    return str(year) if year else "n.d."


def _apa_doi_or_url(paper: dict) -> str:
    doi = str(paper.get("doi") or "").strip()
    if doi:
        if doi.startswith("https://doi.org/"):
            return doi
        return "https://doi.org/" + doi.removeprefix("doi:")
    url = str(
        paper.get("paper_url")
        or paper.get("url")
        or paper.get("openalex_id")
        or ""
    ).strip()
    return url


def _format_apa7_reference(paper: dict) -> tuple:
    """Build an APA 7 reference draft and return (sort_key, reference, warnings)."""
    warnings = []
    authors = paper.get("authors") or []
    author_text = _apa_authors(authors)

    if not author_text:
        author_text = "[Author information unavailable]"
        warnings.append("Author information is missing.")

    year = _apa_year(paper)
    if year == "n.d.":
        warnings.append("Publication year is missing.")

    title = re.sub(r"\s+", " ", str(paper.get("title") or "").strip())
    if not title:
        title = "[Title unavailable]"
        warnings.append("Title is missing.")

    venue = (
        paper.get("journal_or_venue")
        or paper.get("journal")
        or paper.get("venue")
        or ""
    )
    volume = str(paper.get("volume") or "").strip()
    issue = str(paper.get("issue") or "").strip()
    first_page = str(
        paper.get("first_page") or paper.get("page_start") or ""
    ).strip()
    last_page = str(
        paper.get("last_page") or paper.get("page_end") or ""
    ).strip()
    article_number = str(paper.get("article_number") or "").strip()
    doi_or_url = _apa_doi_or_url(paper)

    # APA 7 journal-article structure:
    # Author. (Year). Article title. Journal, volume(issue), page range. DOI
    reference = f"{author_text} ({year}). {title}."

    if venue:
        venue_part = f"*{venue}*"
        if volume:
            venue_part += f", *{volume}*"
            if issue:
                venue_part += f"({issue})"
        elif issue:
            venue_part += f", ({issue})"

        if first_page and last_page:
            pages = first_page if first_page == last_page else f"{first_page}–{last_page}"
            venue_part += f", {pages}"
        elif first_page:
            venue_part += f", {first_page}"
        elif article_number:
            venue_part += f", Article {article_number}"

        reference += f" {venue_part}."
    else:
        warnings.append("Journal or conference venue is missing.")

    if doi_or_url:
        reference += f" {doi_or_url}"
    else:
        warnings.append("DOI and source URL are missing.")

    # Use the first author's surname as the alphabetical sort key.
    first_author = authors[0] if authors else ""
    if "," in str(first_author):
        sort_key = str(first_author).split(",", 1)[0].casefold()
    else:
        tokens = str(first_author).strip().split()
        sort_key = (tokens[-1] if tokens else "").casefold()

    return sort_key, reference, warnings


def generate_bibliography(
    openalex_ids: List[str],
    style: str = "APA 7",
) -> Dict[str, Any]:
    """
    Generate an APA 7 bibliography directly from OpenAlex work IDs.

    The model passes a simple list of IDs, not a serialized JSON metadata payload.
    Metadata is fetched inside this tool to avoid LLM-generated JSON formatting errors.
    """
    if not openalex_ids:
        return {
            "status": "error",
            "message": "No OpenAlex work IDs were supplied.",
        }

    requested_style = (style or "APA 7").strip() or "APA 7"
    normalized = requested_style.casefold().replace(".", "").replace(" ", "")
    if normalized not in {"apa", "apa7", "apaedition7"}:
        return {
            "status": "unsupported_style",
            "requested_style": requested_style,
            "supported_style": "APA 7",
            "message": "This implementation currently supports APA 7 only.",
        }

    papers = []
    retrieval_errors = []

    # Fetch records inside the tool. The model only supplies simple W... identifiers.
    for identifier in openalex_ids[:MAX_RESULTS]:
        work_id = str(identifier).strip().rstrip("/").split("/")[-1]
        if not re.fullmatch(r"W\d+", work_id):
            retrieval_errors.append({
                "id": str(identifier),
                "error": "Invalid OpenAlex work ID. Expected an ID such as W2741809807.",
            })
            continue

        try:
            work = _openalex_get("works/" + quote(work_id, safe=""))
            papers.append(_record(work))
        except Exception as exc:
            retrieval_errors.append({
                "id": work_id,
                "error": f"{type(exc).__name__}: {exc}",
            })

    if not papers:
        return {
            "status": "error",
            "message": "No OpenAlex records could be retrieved; bibliography was not generated.",
            "retrieval_errors": retrieval_errors,
        }

    formatted = []
    metadata_warnings = []

    for paper in papers:
        sort_key, reference, warnings = _format_apa7_reference(paper)
        formatted.append((sort_key, reference))

        if warnings:
            metadata_warnings.append({
                "paper": paper.get("title") or paper.get("openalex_id"),
                "missing_or_review": warnings,
            })

    formatted.sort(key=lambda item: (item[0], item[1].casefold()))
    entries = [reference for _, reference in formatted]

    return {
        "status": "success",
        "style": "APA 7",
        "count": len(entries),
        "entries": entries,
        "markdown_bibliography": "\n\n".join(entries),
        "metadata_warnings": metadata_warnings,
        "retrieval_errors": retrieval_errors,
        "formatting_note": (
            "References were generated from records fetched directly from OpenAlex. "
            "Check author name parsing, title capitalization and missing journal details "
            "against the publisher record before academic submission."
        ),
    }

SYSTEM_PROMPT = """
You are an academic Agentic Research Assistant built using Google ADK and OpenAlex.

RESEARCH WORKFLOW
1. PLAN: State a short plan and choose 1-3 focused research queries.
2. SEARCH: Call search_research_papers sequentially. Do not make redundant calls.
3. SELECT: Deduplicate records by OpenAlex ID or DOI. Select relevant papers.
4. RETRIEVE: Call retrieve_paper_abstracts with a simple list of OpenAlex work IDs.
5. VERIFY: Call verify_paper_sources with a simple list of OpenAlex work IDs.
   Explain that this confirms OpenAlex records, not independent publisher verification
   or peer-review status.
6. SYNTHESIZE: Compare methods, findings and limitations only when supported by
   retrieved abstracts or metadata. Explicitly identify unavailable abstracts.
7. BIBLIOGRAPHY: Whenever the user requests references, citations, sources, works
   cited, or a bibliography, ALWAYS call generate_bibliography.
   - Pass only a simple list of OpenAlex work IDs, for example:
     ["W2741809807", "W3123456789"].
   - Do NOT construct or pass JSON strings containing paper metadata.
   - If no citation style is specified, use the tool's default APA 7.
   - If another style is explicitly requested, explain that this implementation
     currently supports APA 7 only.
   - Present the bibliography entries returned by the tool. Do not improvise them.

TOOL DISCIPLINE
- Use actual tool results; never claim a search or retrieval occurred if it did not.
- Use sequential calls, not parallel calls.
- Do not invent papers, authors, abstracts, DOIs, venues or performance metrics.
- Do not retry 401, 403 or 429 errors repeatedly.
- If the bibliography tool returns retrieval errors, report which IDs failed.
- Do not generate images or diagrams.
- Keep the final report structured and transparent about missing metadata.
"""

root_agent = Agent(
    name="research_assistant",
    model=MODEL,
    description="OpenAlex research-paper discovery, abstract retrieval, verification and bibliography agent",
    instruction=SYSTEM_PROMPT,
    tools=[search_research_papers, retrieve_paper_abstracts, verify_paper_sources, generate_bibliography],
    before_model_callback=rate_limit_before_model,
)
