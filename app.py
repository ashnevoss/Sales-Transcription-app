import streamlit as st
from elevenlabs.client import ElevenLabs
import httpx
from pydub import AudioSegment
import io
import os

# --- 1. STOCK UI SETUP ---
st.set_page_config(page_title="Sales Transcript AI", layout="centered")

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("Settings")
    user_api_key = st.text_input("ElevenLabs API Key", type="password")
    st.divider()
    st.subheader("Credit Estimator")
    dur = st.number_input("Call Duration (minutes)", min_value=0, step=1)
    if dur > 0:
        st.write(f"Estimated Cost: **{dur * 67} credits**")

# --- 3. MAIN INTERFACE ---
st.title("Sales Call Transcriber")
uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a"])

if uploaded_file:
    st.audio(uploaded_file)
    
    if st.button("Start Transcription"):
        if not user_api_key:
            st.error("Please enter your API Key.")
        else:
            try:
                # Load audio using pydub
                audio = AudioSegment.from_file(uploaded_file)
                
                # Chunk settings: 3 minutes (180,000 ms)
                chunk_length = 180000 
                chunks = [audio[i:i + chunk_length] for i in range(0, len(audio), chunk_length)]
                
                full_transcript = []
                client = ElevenLabs(
                    api_key=user_api_key,
                    httpx_client=httpx.Client(timeout=300.0) # Lower timeout because chunks are small
                )

                progress_bar = st.progress(0)
                status_text = st.empty()

                for i, chunk in enumerate(chunks):
                    status_text.info(f"Processing chunk {i+1} of {len(chunks)}...")
                    
                    # Convert chunk to buffer
                    buffer = io.BytesIO()
                    chunk.export(buffer, format="mp3")
                    buffer.seek(0)
                    
                    # Transcribe chunk
                    response = client.speech_to_text.convert(
                        file=buffer,
                        model_id="scribe_v2",
                        diarize=True
                    )
                    full_transcript.append(response.text)
                    progress_bar.progress((i + 1) / len(chunks))

                status_text.empty()
                st.success("Transcription Complete")
                
                final_text = "\n\n".join(full_transcript)
                st.text_area("Full Transcript", value=final_text, height=400)
                st.download_button("Download Transcript", final_text, file_name="transcript.txt")

            except Exception as e:
                st.error(f"Error: {e}")