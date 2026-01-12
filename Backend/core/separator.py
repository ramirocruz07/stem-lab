import sys
import subprocess
import os

input_file = sys.argv[1]
stem_count = int(sys.argv[2])
quality = sys.argv[3]
export_mp3 = bool(int(sys.argv[4]))

args = ["demucs"]

# Stem count logic
if stem_count == 2:
    args += ["--two-stems=vocals"]
elif stem_count == 6:
    args += ["-n", "htdemucs_6s"]

# Quality logic
if quality == "fast":
    args += ["--shifts", "0"]
elif quality == "best":
    args += ["--shifts", "2"]

# Output format
if export_mp3:
    args += ["--mp3", "--mp3-bitrate", "320"]

args.append(input_file)

print("Running:", " ".join(args))
subprocess.run(args)
