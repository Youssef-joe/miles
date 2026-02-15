import os
import torch
import torchaudio

# 1. DEBUG CHECK: Tell us exactly what is happening in the system
print("--- ENVIRONMENT CHECK START ---")
for lib in ["libnvrtc.so.12", "libnppicc.so.12"]:
    path = f"/usr/lib/{lib}"
    if os.path.exists(path):
        print(f"--- SUCCESS: {lib} found in /usr/lib ---")
    else:
        print(f"--- WARNING: {lib} missing from /usr/lib ---")

# 2. SAFETY IMPORT: Try to load the codec without crashing the whole app
try:
    import torchcodec
    print("--- TORCHCODEC LOADED SUCCESSFULLY ---")
except Exception as e:
    print(f"--- TORCHCODEC ERROR: {e} ---")
    # We don't raise here yet so we can see the prints above in the logs!

# 3. YOUR CORE LOGIC
from generator import load_csm_1b, Segment
import watermarking
import base64
from huggingface_hub import hf_hub_download

# Device selection
if torch.cuda.is_available():
    device = "cuda"
    torch.cuda.init() # Wake up the GPU
elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"

print(f"--- INITIALIZING MODEL ON: {device} ---")
generator = load_csm_1b(device=device)

# --- Your Transcripts & Audio Paths (Mario, Exams, etc.) ---
speakers = [0, 1]
transcripts = [
    "like revising for an exam I'd have to try and like keep up the momentum...",
    "like a super Mario level. Like it's very like high detail..."
]

audio_paths = [
    hf_hub_download(repo_id="sesame/csm-1b", filename="prompts/conversational_a.wav"),
    hf_hub_download(repo_id="sesame/csm-1b", filename="prompts/conversational_b.wav")
]

# --- Helper functions and Endpoint ---
def _load_prompt_audio(audio_path, target_sample_rate):
    audio_tensor, sample_rate = torchaudio.load(audio_path)
    if audio_tensor.shape[0] > 1:
        audio_tensor = torch.mean(audio_tensor, dim=0)
    else:
        audio_tensor = audio_tensor.squeeze(0)
    return torchaudio.functional.resample(audio_tensor, sample_rate, target_sample_rate)

def generate_audio(text: str):
    segments = [
        Segment(text=t, speaker=s, audio=_load_prompt_audio(p, generator.sample_rate))
        for t, s, p in zip(transcripts, speakers, audio_paths)
    ]
    audio = generator.generate(text=text, speaker=1, context=segments, max_audio_length_ms=10_000, temperature=0.9)
    
    torchaudio.save("audio.wav", audio.unsqueeze(0).cpu(), generator.sample_rate)
    with open("audio.wav", "rb") as f:
        encoded_data = base64.b64encode(f.read()).decode('utf-8')
    os.remove("audio.wav")
    return {"audio_data": encoded_data, "format": "wav", "encoding": "base64"}