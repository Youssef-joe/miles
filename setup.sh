[cerebrium.deployment]
name = "10-sesame-voice-api-fix"
python_version = "3.11"  # Upgrade from 3.10 - more stable
include = ["main.py", "generator.py", "models.py", "watermarking.py", "__init__.py"]

# Use CUDA base image instead of debian:bookworm-slim
# This has all CUDA 12.1 libs pre-installed, no symlinks needed
docker_base_image_url = "nvidia/cuda:12.1.1-runtime-ubuntu22.04"

[cerebrium.hardware]
gpu_count = 1
compute = "AMPERE_A10"

[cerebrium.scaling]
# Add this - CSM takes forever to download on first boot
response_grace_period = 900  # 15 minutes

[cerebrium.dependencies.apt]
ffmpeg = "latest"
libavcodec-dev = "latest"
libavformat-dev = "latest"
libavutil-dev = "latest"

[cerebrium.dependencies.pip]
# Let Cerebrium install torch properly - don't use shell_commands
torch = "==2.4.0"
torchaudio = "==2.4.0"
huggingface-hub = {version = "latest", extras = ["hf_transfer"]}
hf_transfer = "latest"
soundfile = "latest"
numpy = "1.26.4"
moshi = "latest"  # Sesame depends on this