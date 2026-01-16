import sys
import subprocess

def main():
    input_file = sys.argv[1]
    stem_count = int(sys.argv[2])
    quality = sys.argv[3]
    export_mp3 = bool(int(sys.argv[4]))
    device = sys.argv[5]
    output_dir = sys.argv[6]

    cmd = ["demucs"]

    if stem_count == 2:
        cmd += ["--two-stems=vocals"]
    elif stem_count == 6:
        cmd += ["-n", "htdemucs_6s"]

    if quality == "fast":
        cmd += ["--shifts", "0"]
    elif quality == "best":
        cmd += ["--shifts", "2"]

    if export_mp3:
        cmd += ["--mp3", "--mp3-bitrate", "320"]
    
    if device == "cpu":
        cmd += ["-d", "cpu"]
    elif device == "cuda":
        cmd += ["-d", "cuda"]
    
    if output_dir:
        cmd += ["-o", output_dir]

    cmd.append(input_file)

    print("Running:", " ".join(cmd))
    subprocess.run(cmd)

# 🔐 CRITICAL GUARD
if __name__ == "__main__":
    main()
