import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="IntelliFlow", page_icon="⚡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0d0d0d;
    color: #e0e0e0;
}

.title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2.4rem;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: -0.5px;
}

.subtitle {
    font-size: 0.95rem;
    color: #666;
    margin-top: -8px;
    margin-bottom: 32px;
}

.trace-box {
    background: #111;
    border: 1px solid #222;
    border-radius: 8px;
    padding: 16px 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    color: #888;
    line-height: 1.8;
}

.trace-step {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 4px;
}

.trace-dot {
    color: #00ff88;
    margin-top: 2px;
}

.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #444;
    margin-bottom: 8px;
    margin-top: 24px;
}

.status-success {
    display: inline-block;
    background: #0d2b1a;
    color: #00ff88;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    padding: 4px 12px;
    border-radius: 4px;
    border: 1px solid #00ff8844;
    margin-bottom: 16px;
}

.status-fail {
    display: inline-block;
    background: #2b0d0d;
    color: #ff4444;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    padding: 4px 12px;
    border-radius: 4px;
    border: 1px solid #ff444444;
    margin-bottom: 16px;
}

.attempt-badge {
    display: inline-block;
    background: #1a1a1a;
    color: #888;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    padding: 4px 12px;
    border-radius: 4px;
    border: 1px solid #333;
    margin-left: 8px;
    margin-bottom: 16px;
}

div[data-testid="stTextArea"] textarea {
    background: #111 !important;
    border: 1px solid #333 !important;
    border-radius: 8px !important;
    color: #e0e0e0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.9rem !important;
}

div[data-testid="stTextArea"] textarea:focus {
    border-color: #00ff88 !important;
    box-shadow: 0 0 0 1px #00ff8833 !important;
}

.stButton > button {
    background: #00ff88 !important;
    color: #0d0d0d !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 10px 28px !important;
    letter-spacing: 0.5px !important;
    transition: opacity 0.15s !important;
}

.stButton > button:hover {
    opacity: 0.85 !important;
}

.stCodeBlock {
    border-radius: 8px !important;
}

hr {
    border-color: #1e1e1e !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">IntelliFlow ⚡</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Autonomous coding agent · writes, runs, and self-corrects Python code</div>', unsafe_allow_html=True)

prompt = st.text_area("Describe what you want the code to do", height=100, placeholder="e.g. write a function that finds all prime numbers up to N using a sieve")

run = st.button("Run Agent")

if run:
    if not prompt.strip():
        st.warning("Enter a coding problem first.")
    else:
        with st.spinner("Agent is working..."):
            try:
                response = requests.post(
                    f"{API_URL}/run",
                    json={"user_prompt": prompt},
                    timeout=120
                )
                response.raise_for_status()
                data = response.json()

                st.divider()

                # Status + attempts
                status_class = "status-success" if data["success"] else "status-fail"
                status_text = "✓ Success" if data["success"] else "✗ Failed"
                st.markdown(
                    f'<span class="{status_class}">{status_text}</span>'
                    f'<span class="attempt-badge">{data["attempts"]} attempt{"s" if data["attempts"] != 1 else ""}</span>',
                    unsafe_allow_html=True
                )

                col1, col2 = st.columns([3, 2])

                with col1:
                    st.markdown('<div class="section-label">Generated Code</div>', unsafe_allow_html=True)
                    st.code(data["code"], language="python")

                    st.markdown('<div class="section-label">Output</div>', unsafe_allow_html=True)
                    if data["output"]:
                        st.code(data["output"], language="text")
                    else:
                        st.markdown('<span style="color:#444;font-size:0.85rem;">No output produced.</span>', unsafe_allow_html=True)

                    if data["error"]:
                        st.markdown('<div class="section-label">Error</div>', unsafe_allow_html=True)
                        st.code(data["error"], language="text")

                with col2:
                    st.markdown('<div class="section-label">Agent Reasoning Trace</div>', unsafe_allow_html=True)
                    trace_html = '<div class="trace-box">'
                    for step in data["trace"]:
                        trace_html += f'<div class="trace-step"><span class="trace-dot">›</span><span>{step.strip()}</span></div>'
                    trace_html += '</div>'
                    st.markdown(trace_html, unsafe_allow_html=True)

            except requests.exceptions.ConnectionError:
                st.error("Cannot reach the API. Make sure `uvicorn api:app --reload` is running.")
            except requests.exceptions.Timeout:
                st.error("Request timed out. The agent may still be running.")
            except requests.exceptions.RequestException as e:
                st.error(f"Request failed: {e}")