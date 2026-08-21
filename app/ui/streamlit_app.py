import base64
from html import escape
from pathlib import Path
import sys

import streamlit as st
from streamlit.web.server.websocket_headers import _get_websocket_headers


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKGROUND_IMAGE_PATH = PROJECT_ROOT / "app" / "ui" / "assets" / "advertising_governance_background_light.png"
DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ui.api_client import ApiResult, FastApiClient


st.set_page_config(page_title="Agentic RAG System", page_icon="🔎", layout="wide")


def main() -> None:
    _initialize_session_state()
    _apply_page_theme()
    if not _is_supported_browser():
        _render_supported_browser_message()
        return

    st.title("Agentic RAG System")
    _render_demo_hero()

    client = FastApiClient(_api_base_url())
    _render_api_status(client)

    upload_tab, ask_tab = st.tabs(["Upload documents", "Ask questions"])

    with upload_tab:
        _render_upload_tab(client)

    with ask_tab:
        _render_ask_tab(client)


def _api_base_url() -> str:
    st.sidebar.caption("FastAPI base URL")
    st.sidebar.code(DEFAULT_API_BASE_URL)
    return DEFAULT_API_BASE_URL


def _render_api_status(client: FastApiClient) -> None:
    with st.sidebar:
        st.subheader("API status")
        if st.button("Check health", use_container_width=True):
            result = client.health_check()
            if result.ok:
                st.success(f"Connected to {result.data.get('app_name', 'FastAPI')}")
                st.caption(
                    f"Provider: {result.data.get('llm_provider')} | "
                    f"Chat: {result.data.get('chat_model')} | "
                    f"Embedding: {result.data.get('embedding_model')}"
                )
            else:
                st.error(_error_message(result))


def _is_supported_browser() -> bool:
    user_agent = _request_user_agent()
    if not user_agent:
        return True

    normalized_user_agent = user_agent.lower()
    return "firefox" not in normalized_user_agent and (
        "chrome" in normalized_user_agent and "edg" not in normalized_user_agent
    )


def _request_user_agent() -> str:
    headers = _get_websocket_headers() or {}
    return headers.get("User-Agent", "")


def _render_supported_browser_message() -> None:
    st.markdown(
        """
        <div style="
            max-width: 44rem;
            margin: 8rem auto 0 auto;
            padding: 2rem;
            border-radius: 1rem;
            background: rgba(255,255,255,0.86);
            border: 1px solid rgba(59,130,246,0.30);
            box-shadow: 0 1rem 3rem rgba(37,99,235,0.16);
            color: #0f172a;
        ">
            <p style="
                margin: 0 0 0.75rem 0;
                color: #2563eb;
                font-size: 0.85rem;
                font-weight: 700;
                letter-spacing: 0.12rem;
                text-transform: uppercase;
            ">Agentic RAG System</p>
            <h1 style="margin: 0 0 0.75rem 0; font-size: 2rem;">
                Please open this demo in Chrome
            </h1>
            <p style="margin: 0; font-size: 1.05rem; line-height: 1.5;">
                This capstone UI is optimized and tested for Chrome. Please use
                Chrome for the assessor demo to avoid browser-specific Streamlit
                rendering differences.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _apply_page_theme() -> None:
    image_data = _image_as_base64(BACKGROUND_IMAGE_PATH)
    page_background = (
        f"linear-gradient(rgba(255, 255, 255, 0.40), rgba(232, 244, 255, 0.52)), "
        f"url('data:image/png;base64,{image_data}')"
        if image_data
        else "linear-gradient(rgba(255, 255, 255, 0.40), rgba(232, 244, 255, 0.52))"
    )
    st.markdown(
        f"""
        <style>
            html,
            body,
            .stApp {{
                background-image: {page_background};
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}

            header[data-testid="stHeader"] {{
                background: rgba(248, 252, 255, 0.92);
                border-bottom: 1px solid rgba(96, 165, 250, 0.25);
            }}

            header[data-testid="stHeader"] button,
            header[data-testid="stHeader"] a,
            header[data-testid="stHeader"] span,
            header[data-testid="stHeader"] svg {{
                color: #64748b !important;
                fill: #64748b !important;
                stroke: #64748b !important;
                opacity: 1 !important;
            }}

            [data-testid="stAppViewContainer"] > .main {{
                background: transparent;
            }}

            [data-testid="stDecoration"] {{
                background-image: linear-gradient(90deg, #38bdf8, #60a5fa, #f97316);
            }}

            [data-testid="stSidebar"] {{
                background:
                    linear-gradient(180deg, rgba(240, 248, 255, 0.88), rgba(219, 234, 254, 0.84));
                border-right: 1px solid rgba(96, 165, 250, 0.24);
            }}

            .block-container {{
                background: transparent;
                border: 0;
                border-radius: 0;
                margin-top: 1.5rem;
                padding-top: 2.5rem;
                box-shadow: none;
            }}

            .block-container h1,
            .block-container h2,
            .block-container h3,
            .block-container p,
            .block-container label,
            .block-container span {{
                color: #0f172a;
            }}

            div[data-testid="stFileUploader"] section {{
                background: rgba(255, 255, 255, 0.76);
                border: 1px solid rgba(59, 130, 246, 0.24);
                border-radius: 0.75rem;
            }}

            div[data-testid="stFileUploader"] section,
            div[data-testid="stFileUploader"] section * {{
                color: #0f172a !important;
            }}

            div[data-testid="stFileUploader"] button {{
                background: rgba(255, 255, 255, 0.88);
                border: 1px solid rgba(59, 130, 246, 0.30);
                color: #0f172a !important;
            }}

            .stButton > button[kind="primary"] {{
                background: rgba(255, 255, 255, 0.88);
                border: 1px solid #ff4b4b;
                color: #0f172a !important;
            }}

            .stButton > button[kind="primary"]:hover {{
                background: rgba(255, 245, 245, 0.96);
                border: 1px solid #ff4b4b;
                color: #0f172a !important;
            }}

            .stButton > button:disabled,
            .stButton > button:disabled:hover {{
                background: rgba(226, 232, 240, 0.82);
                border: 1px solid rgba(148, 163, 184, 0.70);
                color: #64748b !important;
                opacity: 1;
            }}

            .app-glass-card {{
                background: linear-gradient(90deg, rgba(255, 255, 255, 0.78), rgba(219, 234, 254, 0.52));
                border: 1px solid rgba(59, 130, 246, 0.34);
                border-radius: 1rem;
                box-shadow: 0 0.75rem 2rem rgba(37, 99, 235, 0.14);
                backdrop-filter: blur(0.25rem);
                padding: 1.25rem 1.5rem;
                margin: 1rem 0 1.25rem 0;
            }}

            .app-glass-card h4 {{
                color: #0f172a;
                margin: 0 0 1rem 0;
            }}

            .answer-card {{
                max-width: 76rem;
            }}

            .answer-body {{
                color: #0f172a;
                font-size: 1.02rem;
                line-height: 1.7;
            }}

            .answer-body ul {{
                margin: 0.6rem 0 0.9rem 1.35rem;
                padding-left: 0.75rem;
            }}

            .answer-body li {{
                margin-bottom: 0.65rem;
            }}

            .answer-subcard {{
                padding: 0.8rem 0.95rem;
                border-radius: 0.65rem;
                background: rgba(255, 255, 255, 0.72);
                border: 1px solid rgba(147, 197, 253, 0.55);
                color: #0f172a;
            }}

        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_demo_hero() -> None:
    st.markdown(
        """
        <div style="
            background: linear-gradient(90deg, rgba(255, 255, 255, 0.78), rgba(219, 234, 254, 0.52));
            border-radius: 1rem;
            padding: 2rem;
            margin: 0.75rem 0 1.5rem 0;
            min-height: 13rem;
            display: flex;
            align-items: center;
            box-shadow: 0 0.75rem 2rem rgba(37, 99, 235, 0.14);
            border: 1px solid rgba(59, 130, 246, 0.34);
            backdrop-filter: blur(0.25rem);
        ">
            <div style="max-width: 44rem;">
                <div style="
                    color: #2563eb;
                    font-size: 0.85rem;
                    font-weight: 700;
                    letter-spacing: 0.12rem;
                    text-transform: uppercase;
                    margin-bottom: 0.65rem;
                ">
                    Local agentic RAG demo
                </div>
                <h2 style="
                    color: #0f172a;
                    font-size: 2.2rem;
                    line-height: 1.15;
                    margin: 0 0 0.75rem 0;
                ">
                    Advertising Campaign Governance
                </h2>
                <p style="
                    color: #1e3a8a;
                    font-size: 1.05rem;
                    line-height: 1.5;
                    margin: 0;
                ">
                    Upload campaign policy, notes, CSV, or Excel files, then ask grounded
                    questions using local retrieval, citations, and agent orchestration.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _image_as_base64(image_path: Path) -> str:
    if not image_path.exists():
        return ""
    return base64.b64encode(image_path.read_bytes()).decode("utf-8")


def _render_upload_tab(client: FastApiClient) -> None:
    st.subheader("Upload a supported document")
    st.write("Supported formats: PDF, TXT, CSV, and XLSX.")

    if st.session_state.upload_in_progress:
        _process_pending_upload(client)
        return

    _render_last_upload_result()

    uploaded_file = st.file_uploader(
        "Choose a document",
        type=["pdf", "txt", "csv", "xlsx"],
    )

    upload_button_disabled = uploaded_file is None
    if st.button("Upload and index", type="primary", disabled=upload_button_disabled):
        st.session_state.last_upload_result = None
        st.session_state.pending_upload = {
            "filename": uploaded_file.name,
            "content": uploaded_file.getvalue(),
            "content_type": uploaded_file.type or "application/octet-stream",
        }
        st.session_state.upload_in_progress = True
        st.rerun()


def _process_pending_upload(client: FastApiClient) -> None:
    upload = st.session_state.get("pending_upload")
    if not upload:
        st.session_state.upload_in_progress = False
        st.rerun()

    st.markdown(
        """
        <style>
            .stButton {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    processing_message = st.empty()
    processing_message.info(f"Processing {upload['filename']}...")
    try:
        with st.spinner("Uploading, extracting, embedding, and indexing the document..."):
            result = client.upload_document(
                filename=upload["filename"],
                content=upload["content"],
                content_type=upload["content_type"],
            )
    finally:
        processing_message.empty()

    st.session_state.upload_in_progress = False
    st.session_state.pending_upload = None
    st.session_state.last_upload_result = result
    st.rerun()


def _render_last_upload_result() -> None:
    result = st.session_state.get("last_upload_result")
    if not result:
        return

    if result.ok:
        data = result.data
        st.success(f"Uploaded and indexed {data.get('filename')}")
        _render_upload_summary(data)
    else:
        st.error(_error_message(result))


def _initialize_session_state() -> None:
    if "upload_in_progress" not in st.session_state:
        st.session_state.upload_in_progress = False
    if "pending_upload" not in st.session_state:
        st.session_state.pending_upload = None
    if "last_upload_result" not in st.session_state:
        st.session_state.last_upload_result = None
    if "ask_in_progress" not in st.session_state:
        st.session_state.ask_in_progress = False


def _render_upload_summary(data: dict) -> None:
    document_id = escape(str(data.get("document_id", "not returned")))
    source_type = escape(str(data.get("source_type", "unknown")).upper())
    extracted_count = escape(str(data.get("extracted_unit_count", 0)))
    schema_count = escape(str(data.get("tabular_schema_count", 0)))
    chunk_count = escape(str(data.get("indexed_chunk_count", 0)))
    status = escape(str(data.get("status", "unknown")))

    st.markdown(
        f"""
        <div class="app-glass-card">
            <h4>Upload summary</h4>
            <div style="display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 1rem; margin-top: 1rem;">
                <div><div style="font-size: 0.85rem; color: #334155; margin-bottom: 0.35rem;">Type</div><div style="font-size: 2rem; line-height: 1.1; color: #0f172a;">{source_type}</div></div>
                <div><div style="font-size: 0.85rem; color: #334155; margin-bottom: 0.35rem;">Extracted units</div><div style="font-size: 2rem; line-height: 1.1; color: #0f172a;">{extracted_count}</div></div>
                <div><div style="font-size: 0.85rem; color: #334155; margin-bottom: 0.35rem;">Tabular schemas</div><div style="font-size: 2rem; line-height: 1.1; color: #0f172a;">{schema_count}</div></div>
                <div><div style="font-size: 0.85rem; color: #334155; margin-bottom: 0.35rem;">Indexed chunks</div><div style="font-size: 2rem; line-height: 1.1; color: #0f172a;">{chunk_count}</div></div>
                <div><div style="font-size: 0.85rem; color: #334155; margin-bottom: 0.35rem;">Status</div><div style="font-size: 2rem; line-height: 1.1; color: #0f172a;">{status}</div></div>
            </div>
            <div style="margin-top: 1.25rem;">
                <div style="font-size: 0.85rem; color: #334155; margin-bottom: 0.35rem;">Document ID</div>
                <code style="display: block; padding: 0.85rem 1rem; border-radius: 0.65rem; background: rgba(255, 255, 255, 0.70); border: 1px solid rgba(59, 130, 246, 0.18); color: #0f172a; overflow-wrap: anywhere;">{document_id}</code>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_ask_tab(client: FastApiClient) -> None:
    st.subheader("Ask a question")
    question = st.text_area(
        "Question",
        value="",
        placeholder="Ask a question about your uploaded documents.",
        height=100,
        disabled=st.session_state.ask_in_progress,
    )
    limit = st.slider(
        "Maximum evidence chunks",
        min_value=1,
        max_value=10,
        value=4,
        disabled=st.session_state.ask_in_progress,
    )

    ask_button_disabled = not question.strip() or st.session_state.ask_in_progress
    if st.button("Ask", type="primary", disabled=ask_button_disabled):
        st.session_state.ask_in_progress = True
        try:
            with st.spinner("Running the agent workflow and preparing a grounded answer..."):
                result = client.ask_question(question=question, limit=limit)
        finally:
            st.session_state.ask_in_progress = False

        if result.ok:
            _render_answer(result.data)
        else:
            st.error(_error_message(result))


def _render_answer(data: dict) -> None:
    status = data.get("status", "unknown")
    status_color = "#166534" if status == "answered" else "#92400e"
    status_background = "rgba(220, 252, 231, 0.78)" if status == "answered" else "rgba(254, 243, 199, 0.78)"
    answer = _render_answer_text(str(data.get("answer", "No answer returned.")))
    trace = data.get("trace") or []
    trace_text = escape(" → ".join(trace)) if trace else "No trace returned."
    citations = data.get("citations") or []
    citation_items = (
        "\n".join(
            _render_citation_item(index, citation)
            for index, citation in enumerate(citations, start=1)
        )
        if citations
        else '<p style="margin: 0; color: #475569;">No citations returned.</p>'
    )

    html = (
        '<div class="app-glass-card answer-card">'
        '<h4>Answer</h4>'
        f'<div class="answer-body">{answer}</div>'
        f'<div style="display: inline-block; margin-top: 1.25rem; padding: 0.55rem 0.8rem; border-radius: 0.65rem; background: {status_background}; color: {status_color}; font-weight: 600;">'
        f'Status: {escape(str(status))}'
        '</div>'
        '<h4 style="margin-top: 1.5rem;">Agent trace</h4>'
        '<div class="answer-subcard" style="font-family: Consolas, \'Courier New\', monospace; font-size: 0.9rem; overflow-wrap: anywhere;">'
        f'{trace_text}'
        '</div>'
        '<h4 style="margin-top: 1.5rem;">Citations</h4>'
        f'<div>{citation_items}</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def _format_location(metadata: dict) -> str:
    if metadata.get("page"):
        return f", page {metadata['page']}"
    if metadata.get("sheet") and metadata.get("row"):
        return f", sheet {metadata['sheet']}, row {metadata['row']}"
    if metadata.get("row"):
        return f", row {metadata['row']}"
    return ""


def _render_answer_text(answer: str) -> str:
    lines = answer.splitlines()
    html_parts: list[str] = []
    list_items: list[str] = []

    def flush_list() -> None:
        if list_items:
            html_parts.append("<ul>" + "".join(list_items) + "</ul>")
            list_items.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_list()
            continue
        if stripped.startswith(("- ", "* ")):
            list_items.append(f"<li>{escape(stripped[2:])}</li>")
        else:
            flush_list()
            html_parts.append(f"<p style=\"margin: 0 0 0.8rem 0;\">{escape(stripped)}</p>")

    flush_list()
    return "".join(html_parts) or "<p>No answer returned.</p>"


def _render_citation_item(index: int, citation: dict) -> str:
    metadata = citation.get("metadata", {})
    source = escape(str(metadata.get("file", "unknown source")))
    location = escape(_format_location(metadata))
    distance = escape(str(citation.get("distance", "not returned")))
    text = escape(str(citation.get("text", "")))

    return (
        '<div class="answer-subcard" style="margin: 0.65rem 0;">'
        f'<div style="font-weight: 650; color: #0f172a;">[{index}] {source}{location}</div>'
        f'<div style="margin-top: 0.6rem; color: #475569; font-size: 0.86rem;">Distance: {distance}</div>'
        f'<div style="margin-top: 0.55rem; color: #0f172a; line-height: 1.55; white-space: pre-wrap;">{text}</div>'
        '</div>'
    )


def _error_message(result: ApiResult) -> str:
    detail = result.data.get("detail") or "Request failed."
    if result.status_code:
        return f"HTTP {result.status_code}: {detail}"
    return str(detail)


if __name__ == "__main__":
    main()
