# Sesame Voice API (CSM 1B)

This project exposes a text-to-speech API using Sesame's `csm-1b` model, with voice conditioning from prompt audio and post-generation watermarking.

## What This Project Does

- Loads `sesame/csm-1b` from Hugging Face.
- Builds context segments with speaker-labeled transcript + prompt audio.
- Generates speech for input text.
- Applies SilentCipher watermarking to generated audio.
- Returns WAV audio as base64 in an API response.

## High-Level Flow

1. `main.py` initializes the model at import time and selects device (`cuda`, `mps`, `cpu`).
2. Two prompt WAV files are downloaded from `sesame/csm-1b` (`conversational_a.wav`, `conversational_b.wav`).
3. `generate_audio(text)` creates contextual `Segment` objects and calls `generator.generate(...)`.
4. `Generator` tokenizes text + audio, autoregressively samples audio codebooks, and decodes waveform audio.
5. `watermarking.watermark(...)` embeds a watermark and resamples audio.
6. The waveform is saved as WAV, base64-encoded, and returned as JSON.

## Project Structure

- `main.py`: service entrypoint and `generate_audio` endpoint function.
- `generator.py`: text/audio tokenization, sampling loop, decode, watermark integration.
- `models.py`: transformer architecture and frame-level generation logic.
- `watermarking.py`: SilentCipher load/watermark/verify helpers.
- `test.py`: client script that calls deployed endpoint and writes `output.wav`.
- `requirements.txt`: local Python dependencies.
- `cerebrium.toml`: deployment config currently used in this repo.
- `setup.sh`: alternate deployment config draft (not a shell script in current form).

## Runtime and Dependencies

### Python

- Local code targets Python `3.10` by current `cerebrium.toml`.
- `setup.sh` draft uses Python `3.11`.

### Core libraries

- `torch`, `torchaudio`, `torchvision`
- `torchtune`, `torchao`, `torchcodec`
- `transformers`, `tokenizers`, `huggingface_hub`
- `moshi`
- `silentcipher` (installed from GitHub in `requirements.txt`)

### System libraries

- `ffmpeg`
- CUDA runtime libs for GPU inference (deployment config includes symlink fixes).

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Authenticate with Hugging Face if needed for model/tokenizer access:

```bash
huggingface-cli login
```

4. Run your service process according to your hosting method (for Cerebrium deployment, use their deployment workflow with `cerebrium.toml`).

## API Contract

### Function

`generate_audio(text: str)` in `main.py`.

### Input

```json
{
  "text": "Hello world"
}
```

### Output

```json
{
  "audio_data": "<base64-wav>",
  "format": "wav",
  "encoding": "base64"
}
```

## Deployment Notes (Cerebrium)

Current deployment configuration is in `cerebrium.toml`:

- Deployment name: `10-sesame-voice-api-v14`
- Python: `3.10`
- GPU: `AMPERE_A10`
- Includes only runtime files (`main.py`, `generator.py`, `models.py`, `watermarking.py`, `__init__.py`)
- Uses shell commands for `silentcipher` install and CUDA/FFmpeg library compatibility symlinks

The `setup.sh` file appears to be an alternative config draft using:

- Python `3.11`
- `nvidia/cuda:12.1.1-runtime-ubuntu22.04`
- Longer response grace period

Use one deployment strategy consistently to avoid config drift.

## Testing the Deployed API

`test.py` posts text to the remote endpoint, decodes base64 audio, and writes `output.wav`.

Run:

```bash
python test.py
```

Notes:

- Update endpoint URL and API key before running.
- Current file has hardcoded secrets and should not be committed in that form.

## Known Risks and Caveats

- Heavy initialization cost: model download and warm-up can be slow.
- GPU expected for practical latency; CPU fallback is supported but slow.
- `main.py` initializes global model state at import time.
- Context prompt audio is fixed to two sample files unless code is changed.
- If CUDA shared libs are missing, `torchcodec` import and audio stack can fail.

## Troubleshooting

### `torchcodec` import errors or missing CUDA libs

- Verify required CUDA runtime libraries are available.
- For containerized deployment, keep CUDA base image + symlink strategy aligned with Torch/Torchaudio versions.

### Very slow first request

- Expected when model/assets are first downloaded.
- Prefer warm instances and adequate response grace period in deployment config.

### Output audio not produced

- Confirm endpoint returns 200.
- Check that response contains `audio_data` under expected JSON path.
- Ensure base64 decode succeeds and WAV write permissions are available.

## Security and Operations

- Rotate and remove any hardcoded API keys from `test.py`.
- Use environment variables or secret management for keys/tokens.
- Pin dependency versions deliberately; mixing Torch/CUDA versions can break runtime compatibility.
- Add health checks and structured logging around model init/generation for production use.

## Suggested Next Improvements

1. Add request schema validation and explicit error responses around `generate_audio`.
2. Move transcripts/speakers/audio prompts to configurable input or server-side presets.
3. Add a local CLI/integration test that does not require the remote deployment endpoint.
4. Add CI checks for formatting, linting, and import-time smoke tests.
