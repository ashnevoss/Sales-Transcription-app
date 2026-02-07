import streamlit as st
from elevenlabs.client import ElevenLabs
import httpx
import threading
import time

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
        # 800 credits / 12 mins = ~67 per min
        st.write(f"Estimated Cost: **{dur * 67} credits**")

# --- 3. MAIN INTERFACE ---
st.title("Sales Call Transcriber")
st.write("Upload your recording to generate a speaker-separated transcript.")

uploaded_file = st.file_uploader("Choose audio file", type=["mp3", "wav", "m4a"])

if uploaded_file:
    st.audio(uploaded_file)
    
    if st.button("Start Transcription"):
        if not user_api_key:
            st.error("Please enter your API Key in the sidebar.")
        else:
            status_placeholder = st.empty()
            # Container to capture data from the background thread
            sync_box = {"data": None, "error": None}

            def run_transcription():
                try:
                    # Setting a massive 30-minute timeout for the whole file
                    client = ElevenLabs(
                        api_key=user_api_key,
                        httpx_client=httpx.Client(timeout=1800.0)
                    )
                    
                    # Scribe v2 handles the full file with diarization
                    result = client.speech_to_text.convert(
                        file=uploaded_file,
                        model_id="scribe_v2",
                        diarize=True 
                    )
                    sync_box["data"] = result
                except Exception as e:
                    sync_box["error"] = str(e)

            # Launch the transcription in the background
            worker_thread = threading.Thread(target=run_transcription)
            worker_thread.start()

            # --- HEARTBEAT LOOP ---
            # This prevents 'Connection Lost' by forcing UI updates every 5 seconds
            start_time = time.time()
            while worker_thread.is_alive():
                elapsed = int(time.time() - start_time)
                status_placeholder.info(f"⏳ AI is processing... {elapsed}s elapsed. Do not close this tab.")
                time.sleep(5) 

            status_placeholder.empty()

            if sync_box["error"]:
                st.error(f"Transcription Failed: {sync_box['error']}")
            else:
                st.success("Transcription Complete!")
                st.text_area("Transcript Output", value=sync_box["data"].text, height=450)
                st.download_button(
                    label="Download as Text File",
                    data=sync_box["data"].text,
                    file_name=f"transcript_{uploaded_file.name}.txt",
                    mime="text/plain"
                )