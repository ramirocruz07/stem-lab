import sys
import subprocess
import torch
import torchaudio
import soundfile as sf

def custom_save(filepath, src, sample_rate, **kwargs):
    src = src.detach().cpu().numpy().T
    sf.write(filepath, src, sample_rate)

torchaudio.save = custom_save

def main():
    input_file = sys.argv[1]
    stem_count = int(sys.argv[2])
    quality = sys.argv[3]
    audio_format = sys.argv[4]
    bitrate = sys.argv[5]
    device = sys.argv[6]
    output_dir = sys.argv[7]
  

    cmd = ["demucs"]

    if stem_count == 2:
        cmd += ["--two-stems=vocals"]
    elif stem_count == 6:
        cmd += ["-n", "htdemucs_6s"]

    if quality == "fast":
        cmd += ["--shifts", "0"]
    elif quality == "best":
        cmd += ["--shifts", "2"]

   
    if device == "cpu":
        cmd += ["-d", "cpu"]
    elif device == "cuda":
        cmd += ["-d", "cuda"]
    
    if output_dir != "":
        cmd += ["-o", output_dir]
    if audio_format=="mp3":
        cmd+=["--mp3"]
        if bitrate:
            cmd+=["--mp3-bitrate",bitrate]

    cmd.append(input_file)

    print("Running:", " ".join(cmd))
    subprocess.run(cmd)

# 🔐 CRITICAL GUARD
if __name__ == "__main__":
    main()
