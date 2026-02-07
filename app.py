import streamlit as st
from elevenlabs.client import ElevenLabs
import httpx

# --- 1. SETTINGS & DARK THEME ---
st.set_page_config(page_title="Sales Transcript AI", page_icon="🎙️", layout="centered")

# Minimal Dark Aesthetic matching your preference
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stButton>button { 
        width: 100%; border-radius: 10px; height: 3.5em; 
        background-color: #1c1f26; color: #00ffa3; border: 1px solid #3e424b; 
        font-weight: bold; transition: 0.3s;
    }
    .stButton>button:hover { border-color: #00ffa3; background-color: #262a33; }
    .stTextArea textarea { background-color: #161920; color: #e0e0e0; border: 1px solid #3e424b; }
    /* Fix for the "Activate Windows" watermark area visibility */
    .main .block-container { padding-bottom: 100px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR FOR API KEY ---
with st.sidebar:
    st.header("🔑 Authentication")
    user_api_key = st.text_input("ElevenLabs API Key", type="password", help="Paste your key here.")
    st.info("Using Scribe v2 Model")
    st.caption("v1.3 - Localhost Timeout Fix")

# --- 3. MAIN INTERFACE ---
st.title("🎙️ Sales Call Transcriber")
st.write("Upload audio to generate a speaker-separated transcript.")

uploaded_file = st.file_uploader("Upload Audio (MP3/WAV/M4A)", type=["mp3", "wav", "m4a"])

if uploaded_file is not None:
    st.success(f"File '{uploaded_file.name}' ({(uploaded_file.size/1024/1024):.2f} MB) loaded.")
    st.audio(uploaded_file)
    
    if st.button("🚀 Start Transcription"):
        if not user_api_key:
            st.error("Please enter your API Key in the sidebar.")
        else:
            try:
                # 1200 second timeout is 20 minutes - enough for long sales calls
                with st.spinner("Processing... This may take a few minutes. Do not close this tab."):
                    client = ElevenLabs(
                        api_key=user_api_key,
                        httpx_client=httpx.Client(
                            timeout=1200.0,
                            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
                        )
                    )
                    
                    # Call ElevenLabs Scribe v2
                    transcription = client.speech_to_text.convert(
                        file=uploaded_file,
                        model_id="scribe_v2",
                        tag_audio_events=True,
                        diarize=True # Separates Rep from Customer
                    )
                    
                    st.success("Transcription Complete!")
                    
                    # --- RESULTS ---
                    st.subheader("Transcript")
                    full_text = transcription.text
                    st.text_area("Full Transcript", value=full_text, height=450)
                    
                    st.download_button(
                        label="📥 Download as .txt",
                        data=full_text,
                        file_name=f"Sales_Transcript_{uploaded_file.name}.txt",
                        mime="text/plain"
                    )

            except Exception as e:
                error_str = str(e)
                if "401" in error_str:
                    st.error("Invalid API Key. Please check your ElevenLabs settings.")
                elif "disconnected" in error_str.lower() or "timeout" in error_str.lower():
                    st.error("Connection lost. Your local server timed out waiting for the response.")
                    st.info("Check the terminal for more details.")
                else:
                    st.error(f"Error: {error_str}")
else:
    st.info("Awaiting file upload...")