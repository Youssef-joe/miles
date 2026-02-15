import argparse
import numpy as np
import argparse
import silentcipher
import torch
import torchaudio

# This watermark key is public, it is not secure.
# If using CSM 1B in another application, use a new private key and keep it secret.
CSM_1B_GH_WATERMARK = [212, 211, 146, 56, 201]


def cli_check_audio() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio_path", type=str, required=True)
    args = parser.parse_args()

    check_audio_from_file(args.audio_path)


def load_watermarker(device: str = "cuda") -> silentcipher.server.Model:
    model = silentcipher.get_model(
        model_type="44.1k",
        device=device,
    )
    return model


@torch.inference_mode()
def watermark(
    watermarker: silentcipher.server.Model,
    audio_array: np.ndarray, # Type hint change
    sample_rate: int,
    watermark_key: list[int],
) -> tuple[np.ndarray, int]:
    # 1. Convert numpy to tensor for resampling
    audio_tensor = torch.from_numpy(audio_array).to(watermarker.device)
    
    # 2. Resample using torchaudio
    audio_44khz = torchaudio.functional.resample(audio_tensor, orig_freq=sample_rate, new_freq=44100)
    
    # 3. Convert back to numpy because silentcipher.encode_wav requires it
    audio_44khz_np = audio_44khz.cpu().numpy()
    
    # 4. Run the watermarker
    encoded_np, _ = watermarker.encode_wav(audio_44khz_np, 44100, watermark_key, calc_sdr=False, message_sdr=36)

    # 5. Convert back to tensor to resample the output
    encoded_tensor = torch.from_numpy(encoded_np).to(watermarker.device)
    output_sample_rate = min(44100, sample_rate)
    encoded_tensor = torchaudio.functional.resample(encoded_tensor, orig_freq=44100, new_freq=output_sample_rate)
    
    # 6. Return as numpy to match the expected flow
    return encoded_tensor.cpu().numpy(), output_sample_rate


@torch.inference_mode()
def verify(
    watermarker: silentcipher.server.Model,
    watermarked_audio: torch.Tensor,
    sample_rate: int,
    watermark_key: list[int],
) -> bool:
    watermarked_audio_44khz = torchaudio.functional.resample(watermarked_audio, orig_freq=sample_rate, new_freq=44100)
    result = watermarker.decode_wav(watermarked_audio_44khz, 44100, phase_shift_decoding=True)

    is_watermarked = result["status"]
    if is_watermarked:
        is_csm_watermarked = result["messages"][0] == watermark_key
    else:
        is_csm_watermarked = False

    return is_watermarked and is_csm_watermarked


def check_audio_from_file(audio_path: str) -> None:
    watermarker = load_watermarker(device="cuda")

    audio_array, sample_rate = load_audio(audio_path)
    is_watermarked = verify(watermarker, audio_array, sample_rate, CSM_1B_GH_WATERMARK)

    outcome = "Watermarked" if is_watermarked else "Not watermarked"
    print(f"{outcome}: {audio_path}")


def load_audio(audio_path: str) -> tuple[torch.Tensor, int]:
    audio_array, sample_rate = torchaudio.load(audio_path)
    audio_array = audio_array.mean(dim=0)
    return audio_array, int(sample_rate)


if __name__ == "__main__":
    cli_check_audio()
