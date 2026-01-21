import sys
import subprocess
import torch
import torchaudio
import soundfile as sf

def custom_save(filepath, src, sample_rate, **kwargs):
    src = src.detach().cpu().numpy().T
    sf.write(filepath, src, sample_rate)

torchaudio.save = custom_save

def check_gpu_availability():
    """Check if CUDA GPU is available"""
    try:
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
            return True, f"{gpu_name} ({gpu_memory:.1f}GB)"
        else:
            return False, "No GPU available"
    except:
        return False, "Error checking GPU"

def main():
    input_file = sys.argv[1]
    stem_count = int(sys.argv[2])
    quality = sys.argv[3]
    audio_format = sys.argv[4]
    bitrate = sys.argv[5]
    requested_device = sys.argv[6]
    output_dir = sys.argv[7]
    
    print(f"\n{'='*50}")
    print(f"STEM SPLITTER - Processing: {input_file}")
    print(f"{'='*50}")
  
    cmd = ["demucs"]

    # Set the model based on stem count
    if stem_count == 2:
        cmd += ["-n", "htdemucs_ft", "--two-stems=vocals"]
        print("Model: HTDemucs FT (2 stems: vocals + instrumental)")
    elif stem_count == 6:
        cmd += ["-n", "htdemucs_6s"]
        print("Model: HTDemucs 6S (6 stems)")
    else:
        cmd += ["-n", "htdemucs"]
        print("Model: HTDemucs (4 stems: vocals, drums, bass, other)")

    # Set quality (shifts)
    if quality == "fast":
        cmd += ["--shifts", "0"]
        print("Quality: Fast (0 shifts)")
    elif quality == "best":
        cmd += ["--shifts", "2"]
        print("Quality: Best (2 shifts)")
    else:  # balanced
        cmd += ["--shifts", "1"]
        print("Quality: Balanced (1 shift)")

    # Handle device selection with intelligent fallback
    gpu_available, gpu_info = check_gpu_availability()
    actual_device = requested_device
    
    if requested_device == "cuda":
        if gpu_available:
            cmd += ["-d", "cuda"]
            print(f"Device: GPU - {gpu_info}")
        else:
            cmd += ["-d", "cpu"]
            actual_device = "cpu"
            print(f"⚠️  GPU requested but not available. Falling back to CPU.")
            print(f"Device: CPU")
    
    elif requested_device == "cpu":
        cmd += ["-d", "cpu"]
        print("Device: CPU")
    
    else:  # auto
        if gpu_available:
            cmd += ["-d", "cuda"]
            actual_device = "cuda"
            print(f"Device: Auto-selected GPU - {gpu_info}")
        else:
            cmd += ["-d", "cpu"]
            actual_device = "cpu"
            print("Device: Auto-selected CPU (GPU not available)")

    # Output directory
    if output_dir != "":
        cmd += ["-o", output_dir]
        print(f"Output directory: {output_dir}")
    else:
        print("Output directory: Default (separated folder in Home)")

    # Audio format
    if audio_format == "mp3":
        cmd += ["--mp3"]
        if bitrate:
            cmd += ["--mp3-bitrate", bitrate]
            print(f"Format: MP3 ({bitrate} kbps)")
        else:
            print("Format: MP3")
    else:
        print("Format: WAV (Lossless)")

    cmd.append(input_file)
    print(f"{'='*50}")

    # Run Demucs
    try:
        print(f"Starting separation with {actual_device.upper()}...")
        print(f"Command: {' '.join(cmd[:12])}...")  # Show truncated command
        
        # Run with real-time output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Print output in real-time
        for line in process.stdout:
            line = line.strip()
            if line:  # Only print non-empty lines
                print(line)
        
        process.wait()
        
        if process.returncode == 0:
            print(f"\n✅ Separation completed successfully with {actual_device.upper()}!")
        else:
            print(f"\n⚠️  Separation completed with return code: {process.returncode}")
            
    except Exception as e:
        print(f"\n❌ Error during separation: {e}")
        
        # GPU fallback: If GPU failed, try CPU
        if requested_device == "cuda" and actual_device == "cuda":
            print("\n🔄 GPU failed, trying CPU as fallback...")
            cmd = [c for c in cmd if c not in ["-d", "cuda"]]
            cmd += ["-d", "cpu"]
            subprocess.run(cmd)
        else:
            print("Please check your input file and settings.")

if __name__ == "__main__":
    main()