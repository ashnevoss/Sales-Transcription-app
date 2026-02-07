import streamlit as st
from elevenlabs.client import ElevenLabs
import httpx

# --- 1. PAGE CONFIG & DARK THEME ---
st.set_page_config(
    page_title="Sales Transcript AI",
    page_icon="🎙️",
    layout="centered"
)

st.markdown("""
    <style>
    /* Dark Theme Overrides */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3.5em;
        background-color: #1c1f26;
        color: white;
        border: 1px solid #3e424b;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        border-color: #00ffa3;
        color: #00ffa3;
        background-color: #262a33;
    }
    .stTextArea textarea {
        background-color: #161920 !important;
        color: #00ffa3 !important;
        border: 1px solid #3e424b !important;
        font-family: 'Courier New', Courier, monospace;
    }
    /* Hide Streamlit Header/Footer for a cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER ---
st.title("🎙️ Sales Call Transcriber")
st.markdown("---")

# --- 3. SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("🔑 Authentication")
    api_key = st.text_input("ElevenLabs API Key", type="password", help="Get this from your ElevenLabs profile settings.")
    
    st.header("⚙️ Model Settings")
    diarize = st.checkbox("Distinguish Speakers", value=True, help="Separates 'Speaker 1' from 'Speaker 2'. Perfect for Sales Calls.")
    model_choice = st.selectbox("Model", ["scribe_v2"], index=0)
    
    st.markdown("---")
    st.caption("Powered by ElevenLabs Scribe v2")

# --- 4. MAIN INTERFACE ---
uploaded_file = st.file_uploader("Upload Sales Call Recording", type=["mp3", "wav", "m4a", "ogg"])

if uploaded_file:
    # Playback for verification
    st.audio(uploaded_file)
    
    if st.button("🚀 Start Transcription"):
        if not api_key:
            st.warning("Please provide an API Key in the sidebar.")
        else:
            try:
                with st.spinner("Analyzing audio... This may take a few minutes for longer calls."):
                    # We use a custom httpx client to ensure the timeout is long enough (10 minutes)
                    # This prevents the 'Server disconnected' error.
                    client = ElevenLabs(
                        api_key=api_key,
                        httpx_client=httpx.Client(timeout=600.0) 
                    )
                    
                    # Convert audio to text
                    transcription = client.speech_to_text.convert(
                        file=uploaded_file,
                        model_id=model_choice,
                        tag_audio_events=True,
                        diarize=diarize
                    )
                    
                    st.success("Analysis Complete!")
                    
                    # --- 5. RESULTS ---
                    st.subheader("Final Transcript")
                    
                    # If diarization is on, formatted text usually comes back with speaker tags
                    full_text = transcription.text
                    
                    st.text_area(
                        label="Raw Text (Copy/Paste)",
                        value=full_text,
                        height=450
                    )
                    
                    # Download functionality
                    st.download_button(
                        label="📥 Download as Text File",
                        data=full_text,
                        file_name=f"Sales_Call_{uploaded_file.name}.txt",
                        mime="text/plain"
                    )

            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg:
                    st.error("Invalid API Key. Please check your ElevenLabs settings.")
                elif "429" in error_msg:
                    st.error("Quota exceeded! The free tier has limits on how much you can transcribe.")
                else:
                    st.error(f"Error: {error_msg}")
                    st.info("Tip: If the file is very large, try converting it to a lower-bitrate MP3.")

else:
    st.info("Please upload an audio file to begin.")