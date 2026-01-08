import sys
import subprocess

file = sys.argv[1]

subprocess.run([
    "demucs",
    file
])
