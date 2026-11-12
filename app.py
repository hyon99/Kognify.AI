import asyncio
import importlib
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

# Make imports independent of the shell's current working directory.
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

st.set_page_config(
    page_title="Kognify AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

APP_NAME = "kognify_ai"
AGENT_MODULE = os.getenv("ADK_AGENT_MODULE", "research_assistant.agent")

# ---------- Styling ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@1,600&display=swap');

:root {
  --ink: #050505;
  --muted: #a7a7ad;
  --cyan: #27d7ee;
  --violet: #8b5cf6;
  --pink: #d05de6;
}
html, body, [data-testid="stAppViewContainer"] {
  background: #050505 !important;
  font-family: 'DM Sans', sans-serif;
}
[data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer {
  visibility: hidden !important;
}
.block-container {
  max-width: 100% !important;
  padding: 0 !important;
}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:first-child {
  display: none !important;
}
[data-testid="stHorizontalBlock"] {
  gap: 0 !important;
}
section.main > div { padding: 0 !important; }
div[data-testid="column"] { padding: 0 !important; }

[class*="st-key-sidebar_panel"] {
  position: relative;
  min-height: 100vh;
  height: 100vh;
  background: #030303;
  color: #f4f4f4;
  padding: 36px 30px 28px 42px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}
.brand {
  font-weight: 800;
  font-size: clamp(22px, 2.2vw, 30px);
  letter-spacing: -1.2px;
  color: #f4ffd1;
  margin: 2px 0 25px 0;
  padding-right: 56px;
}
.brand span {
  background: linear-gradient(110deg, #22d3ee, #a855f7);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.nav-hint {
  color: #77777e;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  margin: 25px 0 8px 4px;
}
div.stButton > button {
  width: 100%;
  text-align: left;
  background: transparent;
  color: #bdbdc2;
  border: 0;
  border-radius: 10px;
  padding: 11px 12px;
  font-size: 15px;
  font-weight: 500;
  transition: all .18s ease;
}
div.stButton > button:hover {
  background: #17171b;
  color: white;
  border: 0;
}
div.stButton > button:focus {
  box-shadow: none;
  border: 0;
  color: white;
}
[class*="st-key-nav_close"] button,
[class*="st-key-nav_open"] button {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 40px !important;
  min-width: 40px !important;
  height: 40px !important;
  min-height: 40px !important;
  padding: 0 !important;
  text-align: center !important;
  border-radius: 50% !important;
  background: rgba(255,255,255,.1) !important;
  color: #fff !important;
}
[class*="st-key-nav_open"] {
  position: fixed !important;
  top: 15px !important;
  left: 5vw !important;
  z-index: 1100 !important;
}
[class*="st-key-nav_close"] {
  position: absolute !important;
  top: 34px !important;
  right: 22px !important;
  z-index: 2 !important;
}
.sidebar-foot {
  margin-top: auto;
  color: #696970;
  font-size: 11px;
  letter-spacing: .3px;
  padding: 16px 4px 0;
}
[class*="st-key-workspace_panel"] {
  min-height: 100vh;
  height: 100vh;
  background: linear-gradient(120deg, #273b9b, #6945b8, #9b45c7, #2869bd, #273b9b);
  background-size: 300% 300%;
  animation: kognifyGradient 18s ease-in-out infinite;
  color: white;
  box-sizing: border-box;
  padding: 0 clamp(26px, 5vw, 76px);
  position: relative;
  isolation: isolate;
  overflow: hidden;
}
[class*="st-key-workspace_panel"]::before,
[class*="st-key-workspace_panel"]::after {
  content: "";
  position: absolute;
  z-index: -1;
  width: 62vmax;
  height: 62vmax;
  border-radius: 50%;
  filter: blur(75px);
  opacity: .34;
  pointer-events: none;
  will-change: transform;
}
[class*="st-key-workspace_panel"]::before {
  top: -34vmax;
  left: -18vmax;
  background: radial-gradient(circle, rgba(37, 211, 238, .95) 0%, rgba(70, 91, 220, .48) 35%, transparent 70%);
  animation: kognifyBlobOne 22s ease-in-out infinite alternate;
}
[class*="st-key-workspace_panel"]::after {
  right: -24vmax;
  bottom: -38vmax;
  background: radial-gradient(circle, rgba(204, 85, 238, .95) 0%, rgba(123, 70, 210, .52) 38%, transparent 72%);
  animation: kognifyBlobTwo 26s ease-in-out infinite alternate;
}
@keyframes kognifyGradient {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
@keyframes kognifyBlobOne {
  0% { transform: translate3d(-4vw, 2vh, 0) scale(.92); }
  50% { transform: translate3d(24vw, 23vh, 0) scale(1.12); }
  100% { transform: translate3d(42vw, 5vh, 0) scale(.98); }
}
@keyframes kognifyBlobTwo {
  0% { transform: translate3d(5vw, -3vh, 0) scale(1.02); }
  50% { transform: translate3d(-26vw, -22vh, 0) scale(.9); }
  100% { transform: translate3d(-40vw, -4vh, 0) scale(1.14); }
}
@media (prefers-reduced-motion: reduce) {
  [class*="st-key-workspace_panel"],
  [class*="st-key-workspace_panel"]::before,
  [class*="st-key-workspace_panel"]::after {
    animation: none !important;
  }
}
.workspace-inner {
  max-width: 980px;
  margin: 0 auto;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.topline {
  display:flex;
  justify-content:space-between;
  align-items:center;
  padding-top: 25px;
  color: rgba(255,255,255,.72);
  font-size: 12px;
  letter-spacing: .7px;
  text-transform: uppercase;
}
.topline.menu-closed {
  padding-left: 56px;
}
[class*="st-key-workspace_panel"] > [data-testid="stElementContainer"]:has(.hero) {
  display: flex !important;
  flex: 1 1 auto !important;
  flex-direction: column !important;
  justify-content: center !important;
}
.hero {
  margin: 0;
  text-align: center;
  padding-top: 0;
}
.hero-kicker {
  font-size: 11px;
  letter-spacing: 3px;
  text-transform: uppercase;
  opacity: .72;
  margin-bottom: 18px;
}
.hero h1 {
  font-family: 'Playfair Display', Georgia, serif;
  font-style: italic;
  font-weight: 600;
  font-size: clamp(29px, 3vw, 42px);
  line-height: 1.2;
  margin: 0;
  color: #fff;
  text-shadow: 0 2px 18px rgba(44,20,90,.12);
}
.hero p {
  font-size: 14px;
  color: rgba(255,255,255,.78);
  margin-top: 14px;
}
/* Responsive, full-width ChatGPT-style composer.
   The composer itself is the pill; there is no separate outer white capsule. */
div[data-testid="stChatInput"] {
  box-sizing: border-box !important;
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  gap: 10px !important;
  width: 100% !important;
  max-width: 920px !important;
  min-width: 0 !important;
  margin: 18px auto !important;
  padding: 7px 7px 7px 16px !important;
  background: #ffffff !important;
  border: 1px solid rgba(35, 30, 60, .12) !important;
  border-radius: 999px !important;
  outline: none !important;
  box-shadow: 0 10px 30px rgba(32,20,80,.14) !important;
  overflow: visible !important;
  transition: background .2s ease, border-color .2s ease, box-shadow .2s ease !important;
}
div[data-testid="stChatInput"]:focus-within {
  border-color: rgba(93, 89, 214, .34) !important;
  box-shadow: 0 0 0 3px rgba(93, 89, 214, .10), 0 12px 30px rgba(32, 20, 80, .15) !important;
}

/* Force Streamlit's inner layout and textarea to use all remaining width. */
div[data-testid="stChatInput"] > div {
  box-sizing: border-box !important;
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  flex: 1 1 0% !important;
  width: 100% !important;
  min-width: 0 !important;
  max-width: none !important;
  padding: 0 !important;
  background: transparent !important;
  border: 0 !important;
  outline: 0 !important;
  box-shadow: none !important;
}
div[data-testid="stChatInput"] > div > div:first-child {
  display: flex !important;
  flex: 1 1 0% !important;
  flex-direction: row !important;
  width: 100% !important;
  min-width: 0 !important;
  align-items: center !important;
  justify-content: space-between !important;
}
div[data-testid="stChatInput"] [data-baseweb="textarea"] {
  box-sizing: border-box !important;
  flex: 1 1 0% !important;
  width: 100% !important;
  min-width: 0 !important;
  max-width: none !important;
  background: transparent !important;
  border: 0 !important;
  outline: 0 !important;
  box-shadow: none !important;
}
div[data-testid="stChatInput"] textarea,
div[data-testid="stChatInput"] textarea:focus {
  box-sizing: border-box !important;
  display: block !important;
  width: 100% !important;
  min-width: 0 !important;
  color: #242235 !important;
  -webkit-text-fill-color: #242235 !important;
  caret-color: #7654d8 !important;
  background: transparent !important;
  border: 0 !important;
  outline: 0 !important;
  box-shadow: none !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 15px !important;
  line-height: 1.5 !important;
  text-align: left !important;
  padding: 8px 3px !important;
  min-height: 40px !important;
  max-height: 140px !important;
  resize: none !important;
}
div[data-testid="stChatInput"] textarea::placeholder {
  color: #777486 !important;
  -webkit-text-fill-color: #777486 !important;
  opacity: 1 !important;
  text-align: left !important;
  font-size: 13px !important;
  letter-spacing: .25px !important;
  text-transform: none !important;
}

/* Follow the user's operating-system/browser colour preference. */
@media (prefers-color-scheme: dark) {
  div[data-testid="stChatInput"] {
    background: #202027 !important;
    border-color: rgba(255,255,255,.10) !important;
    box-shadow: 0 10px 30px rgba(0,0,0,.22) !important;
  }
  div[data-testid="stChatInput"] textarea,
  div[data-testid="stChatInput"] textarea:focus {
    color: #f7f6ff !important;
    -webkit-text-fill-color: #f7f6ff !important;
    caret-color: #b8a1ff !important;
  }
  div[data-testid="stChatInput"] textarea::placeholder {
    color: #aaa7b8 !important;
    -webkit-text-fill-color: #aaa7b8 !important;
  }
}

/* Send button */
div[data-testid="stChatInput"] button {
  box-sizing: border-box !important;
  flex: 0 0 56px !important;
  width: 56px !important;
  min-width: 56px !important;
  height: 40px !important;
  min-height: 40px !important;
  color: #ffffff !important;
  background: linear-gradient(135deg, #5d59d6, #a34fda) !important;
  border: 0 !important;
  border-radius: 999px !important;
  margin: 0 !important;
  padding: 0 !important;
  box-shadow: 0 5px 14px rgba(105,72,195,.24) !important;
  transition: filter .18s ease, transform .18s ease !important;
}
div[data-testid="stChatInput"] button:hover {
  filter: brightness(1.08);
  transform: translateY(-1px);
}
div[data-testid="stChatInput"] button:focus,
div[data-testid="stChatInput"] button:focus-visible {
  outline: none !important;
  box-shadow: 0 0 0 3px rgba(132,102,230,.2) !important;
}
div[data-testid="stChatInput"] button svg {
  transform: rotate(90deg) !important;
}

/* Desktop: broad input. Tablet and phone: use the full available content width. */
@media (min-width: 1000px) {
  div[data-testid="stChatInput"] {
    max-width: 920px !important;
    padding-left: 18px !important;
    padding-right: 7px !important;
  }
}
@media (max-width: 999px) {
  div[data-testid="stChatInput"] {
    max-width: 100% !important;
    margin: 14px auto !important;
    border-radius: 999px !important;
  }
}
@media (max-width: 600px) {
  div[data-testid="stChatInput"] {
    gap: 8px !important;
    padding: 6px 6px 6px 12px !important;
    border-radius: 999px !important;
  }
  div[data-testid="stChatInput"] textarea,
  div[data-testid="stChatInput"] textarea:focus {
    font-size: 14px !important;
    min-height: 36px !important;
    padding: 7px 2px !important;
  }
  div[data-testid="stChatInput"] textarea::placeholder {
    font-size: 12px !important;
  }
  div[data-testid="stChatInput"] button {
    flex-basis: 50px !important;
    width: 50px !important;
    min-width: 50px !important;
    height: 36px !important;
    min-height: 36px !important;
    border-radius: 999px !important;
  }
}
.chat-area {
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
}
[data-testid="stChatMessage"] {
  background: rgba(255,255,255,.13);
  border: 1px solid rgba(255,255,255,.14);
  border-radius: 16px;
  padding: 14px 16px;
  color: white;
}
[data-testid="stChatMessage"] p { color: white; }
.response-tools {
  color: rgba(255,255,255,.7);
  font-size: 12px;
}
.section-title {
  font-size: 23px;
  font-weight: 700;
  margin: 28px 0 8px;
}
.section-sub {
  color: rgba(255,255,255,.76);
  font-size: 13px;
  margin-bottom: 22px;
}
div[data-testid="stAlert"] { border-radius: 12px; }
@media (max-width: 800px) {
  [class*="st-key-sidebar_panel"] {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 1000;
    width: min(340px, 88vw);
    min-height: 100vh;
    height: 100vh;
    padding: 20px 18px;
    overflow-y: auto;
    box-shadow: 16px 0 38px rgba(0,0,0,.4);
  }
  [class*="st-key-nav_close"] {
    top: 20px !important;
    right: 18px !important;
  }
  [class*="st-key-workspace_panel"] { min-height: 100vh; min-height: 100dvh; height: auto; padding: 0 18px; }
  .brand { margin-bottom: 8px; }
  .hero { padding-top: 0; }
}
@media (max-width: 600px) {
  .topline.menu-closed span:last-child { display: none; }
}
</style>
""", unsafe_allow_html=True)

# ---------- Session state ----------
defaults = {
    "messages": [],
    "saved_items": [],
    "active_page": "New chat",
    "menu_open": True,
    "user_id": str(uuid.uuid4()),
    "session_id": None,
    "runner": None,
    "agent_error": None,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------- ADK bridge ----------
def get_runner():
    if st.session_state.runner is not None:
        return st.session_state.runner
    try:
        agent_module = importlib.import_module(AGENT_MODULE)
        root_agent = getattr(agent_module, "root_agent", None)
        if root_agent is None:
            # Also support projects that expose the agent as `agent`.
            root_agent = getattr(agent_module, "agent", None)
        if root_agent is None:
            raise AttributeError(
                f"No `root_agent` found in {AGENT_MODULE}. Export root_agent from agent.py."
            )
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService

        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service,
        )
        st.session_state.runner = (runner, session_service)
        return st.session_state.runner
    except Exception as exc:
        if isinstance(exc, ModuleNotFoundError) and exc.name == "research_assistant":
            raise ModuleNotFoundError(
                "Cannot find the research_assistant package. Make sure the folder "
                "'research_assistant' is in the same directory as app.py and contains "
                "'__init__.py' and 'agent.py'. Expected path: "
                f"{PROJECT_ROOT / 'research_assistant'}"
            ) from exc
        st.session_state.agent_error = str(exc)
        raise

async def ensure_adk_session(runner, session_service):
    if st.session_state.session_id is None:
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=st.session_state.user_id,
        )
        st.session_state.session_id = session.id

async def ask_agent(prompt: str) -> str:
    runner, session_service = get_runner()
    await ensure_adk_session(runner, session_service)
    from google.genai import types

    message = types.Content(
        role="user",
        parts=[types.Part(text=prompt)],
    )
    output_parts = []
    async for event in runner.run_async(
        user_id=st.session_state.user_id,
        session_id=st.session_state.session_id,
        new_message=message,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if getattr(part, "text", None):
                    output_parts.append(part.text)
    answer = "\n\n".join(part for part in output_parts if part.strip()).strip()
    return answer or "The assistant returned no text. Please try again."

def start_new_chat():
    st.session_state.messages = []
    st.session_state.session_id = None
    st.session_state.active_page = "New chat"

# ---------- Layout ----------
if st.session_state.menu_open:
  menu_column, main_column = st.columns([0.385, 0.615], gap="small")
else:
  main_column = st.container()
  menu_column = None

if menu_column is not None:
  with menu_column:
    with st.container(key="sidebar_panel"):
      st.markdown('<div class="brand">KOGNIFY <span>AI</span></div>', unsafe_allow_html=True)
      if st.button("×", key="nav_close", help="Close menu"):
        st.session_state.menu_open = False
        st.rerun()

      if st.button("✎   New chat", key="nav_new"):
        start_new_chat()
        st.rerun()
      if st.button("◷   Scheduled", key="nav_scheduled"):
        st.session_state.active_page = "Scheduled"
        st.rerun()
      if st.button("▤   Library", key="nav_library"):
        st.session_state.active_page = "Library"
        st.rerun()
      if st.button("◎   Plugins", key="nav_plugins"):
        st.session_state.active_page = "Plugins"
        st.rerun()
      if st.button("···   Explore", key="nav_explore"):
        st.session_state.active_page = "Explore"
        st.rerun()

      st.markdown('<div class="sidebar-foot">KOGNIFY AI  ·  RESEARCH, REIMAGINED</div>', unsafe_allow_html=True)

with main_column:
  with st.container(key="workspace_panel"):
    if st.session_state.menu_open:
      st.markdown(
        '<div class="topline"><span>✦ Kognify AI</span><span>Agentic research assistant</span></div>',
        unsafe_allow_html=True,
      )
    else:
      title_column, menu_toggle_column = st.columns([0.9, 0.1], gap="small")
      with title_column:
        st.markdown(
          '<div class="topline menu-closed"><span>✦ Kognify AI</span><span>Agentic research assistant</span></div>',
          unsafe_allow_html=True,
        )
      with menu_toggle_column:
        if st.button("☰", key="nav_open", help="Open menu"):
          st.session_state.menu_open = True
          st.rerun()

    page = st.session_state.active_page

    if page == "New chat":
        if not st.session_state.messages:
            st.markdown("""
            <div class="hero">
              <div class="hero-kicker">A little curiosity goes a long way</div>
              <h1>What's worth discovering today?</h1>
              <p>Ask a question. Explore the evidence. Find your next insight.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="chat-area">', unsafe_allow_html=True)
            st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)
            for index, message in enumerate(st.session_state.messages):
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    if message["role"] == "assistant":
                        if st.button("＋ Save to Library", key=f"save_{index}"):
                            st.session_state.saved_items.append({
                                "title": next(
                                    (m["content"][:90] for m in st.session_state.messages[:index]
                                     if m["role"] == "user"),
                                    "Research response"
                                ),
                                "content": message["content"],
                                "saved_at": datetime.now().strftime("%d %b %Y, %H:%M"),
                            })
                            st.toast("Saved to your Library")
            st.markdown('</div>', unsafe_allow_html=True)

        prompt = st.chat_input("Type here to dive deep...", width="stretch")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner("Kognify is investigating..."):
                try:
                    answer = asyncio.run(ask_agent(prompt))
                except Exception as exc:
                    answer = (
                        "I couldn't connect to your ADK research agent.\n\n"
                        f"**Details:** `{exc}`\n\n"
                        "Check that `research_assistant/agent.py` exports `root_agent`, "
                        "your `.env` contains the required API key, and the dependencies are installed."
                    )
                st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

    elif page == "Scheduled":
        st.markdown('<div class="section-title">Scheduled</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Plan recurring research tasks and follow-ups.</div>', unsafe_allow_html=True)
        st.info("Scheduled research is not connected yet. This section is reserved for future recurring research workflows.")

    elif page == "Library":
        st.markdown('<div class="section-title">Your Library</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Research responses you choose to keep.</div>', unsafe_allow_html=True)
        if not st.session_state.saved_items:
            st.info("Your library is empty. Save an assistant response to keep it here.")
        else:
            for i, item in enumerate(reversed(st.session_state.saved_items)):
                with st.expander(f"{item['title']}  ·  {item['saved_at']}", expanded=False):
                    st.markdown(item["content"])

    elif page == "Plugins":
        st.markdown('<div class="section-title">Research tools</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Capabilities available through your connected ADK agent.</div>', unsafe_allow_html=True)
        cards = [
            ("01", "Paper discovery", "Search academic works through OpenAlex."),
            ("02", "Abstract retrieval", "Retrieve and reconstruct available paper abstracts."),
            ("03", "Source verification", "Check that a paper record exists in its source index."),
            ("04", "Bibliography", "Generate formatted references, with APA 7 as the default."),
        ]
        for number, title, desc in cards:
            st.markdown(
                f'<div style="padding:17px 18px;margin:10px 0;border:1px solid rgba(255,255,255,.2);'
                f'border-radius:14px;background:rgba(255,255,255,.09)">'
                f'<span style="opacity:.7;font-size:11px">{number}</span>'
                f'<div style="font-weight:700;font-size:16px;margin:4px 0">{title}</div>'
                f'<div style="font-size:13px;opacity:.8">{desc}</div></div>',
                unsafe_allow_html=True,
            )

    elif page == "Explore":
        st.markdown('<div class="section-title">Explore</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">A few starting points for your next research session.</div>', unsafe_allow_html=True)
        ideas = [
            "Find recent research on lightweight object detection for edge devices.",
            "Compare transformer-based and CNN-based image classification methods.",
            "Identify research gaps in multi-agent systems for academic literature review.",
            "Find papers on retrieval-augmented generation and evaluate their approaches.",
        ]
        for i, idea in enumerate(ideas):
            if st.button(f"↗  {idea}", key=f"idea_{i}"):
                st.session_state.active_page = "New chat"
                st.session_state.messages.append({"role": "user", "content": idea})
                with st.spinner("Kognify is investigating..."):
                    try:
                        answer = asyncio.run(ask_agent(idea))
                    except Exception as exc:
                        answer = f"Could not connect to the ADK agent: `{exc}`"
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                st.rerun()

