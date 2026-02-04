import sys
import os
import torch
import torchaudio
import soundfile as sf
import time

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

def separate_with_api(input_file, stem_count, quality, audio_format, bitrate, requested_device, output_dir):
    """Use demucs Python API for separation"""
    try:
        from demucs.api import Separator
        from demucs.audio import save_audio
        
        print(f"[API] Using demucs Python API for separation")
        
        # Determine model name
        if stem_count == 2:
            model_name = "htdemucs_ft"
            print(f"Model: HTDemucs FT (2 stems: vocals + instrumental)")
        elif stem_count == 6:
            model_name = "htdemucs_6s"
            print(f"Model: HTDemucs 6S (6 stems)")
        else:
            model_name = "htdemucs"
            print(f"Model: HTDemucs (4 stems: vocals, drums, bass, other)")
        
        # Determine shifts
        if quality == "fast":
            shifts = 0
            print(f"Quality: Fast (0 shifts)")
        elif quality == "best":
            shifts = 2
            print(f"Quality: Best (2 shifts)")
        else:  # balanced
            shifts = 1
            print(f"Quality: Balanced (1 shift)")
        
        # Determine device
        gpu_available, gpu_info = check_gpu_availability()
        if requested_device == "cuda":
            if gpu_available:
                device = "cuda"
                print(f"Device: GPU - {gpu_info}")
            else:
                device = "cpu"
                print(f"⚠️  GPU requested but not available. Falling back to CPU.")
                print(f"Device: CPU")
        elif requested_device == "cpu":
            device = "cpu"
            print("Device: CPU")
        else:  # auto
            if gpu_available:
                device = "cuda"
                print(f"Device: Auto-selected GPU - {gpu_info}")
            else:
                device = "cpu"
                print("Device: Auto-selected CPU (GPU not available)")
        
        # Set output format
        if audio_format == "mp3":
            ext = ".mp3"
            bitrate_str = bitrate if bitrate else "320"
            print(f"Format: MP3 ({bitrate_str} kbps)")
        else:
            ext = ".wav"
            bitrate_str = None
            print(f"Format: WAV (Lossless)")
        
        # Create separator
        print(f"Loading model...")
        start_load = time.time()
        separator = Separator(
            model=model_name, 
            device=device, 
            shifts=shifts,
            progress=True
        )
        load_time = time.time() - start_load
        print(f"Model loaded in {load_time:.1f}s")
        
        # Set output directory
        if output_dir and output_dir != "":
            base_output = output_dir
        else:
            base_output = os.path.join(os.path.expanduser("~"), "separated")
        
        output_path = os.path.join(base_output, model_name, os.path.splitext(os.path.basename(input_file))[0])
        os.makedirs(output_path, exist_ok=True)
        print(f"Output directory: {output_path}")
        
        # Process the file
        print(f"{'='*50}")
        print(f"Starting separation...")
        start_sep = time.time()
        
        # This is where the actual separation happens
        origin, separated = separator.separate_audio_file(input_file)
        
        sep_time = time.time() - start_sep
        print(f"Separation completed in {sep_time:.1f}s")
        
        # Save outputs
        print("Saving stems...")
        start_save = time.time()
        
        for stem, source in separated.items():
            if stem_count == 2 and stem != "vocals":
                # For 2-stem mode, we want "vocals" and "other" becomes "instrumental"
                if stem != "other":
                    continue
                output_file = os.path.join(output_path, f"instrumental{ext}")
                stem_display = "instrumental"
            else:
                output_file = os.path.join(output_path, f"{stem}{ext}")
                stem_display = stem
            
            # Configure save parameters for MP3
            save_kwargs = {}
            if audio_format == "mp3" and bitrate_str:
                save_kwargs["bitrate"] = bitrate_str
            
            save_audio(source, output_file, samplerate=separator.samplerate, **save_kwargs)
            print(f"  ✓ Saved: {stem_display}")
        
        save_time = time.time() - start_save
        
        total_time = time.time() - start_load
        print(f"{'='*50}")
        print(f"✅ Separation completed successfully!")
        print(f"Total time: {total_time:.1f}s (load: {load_time:.1f}s, separate: {sep_time:.1f}s, save: {save_time:.1f}s)")
        print(f"Output saved to: {output_path}")
        
        return output_path
        
    except ImportError as e:
        print(f"[API ERROR] Failed to import demucs API: {e}")
        raise
    except Exception as e:
        print(f"[API ERROR] Separation failed: {e}")
        import traceback
        traceback.print_exc()
        raise

def separate_with_subprocess(input_file, stem_count, quality, audio_format, bitrate, requested_device, output_dir):
    """Fallback to subprocess method if API fails"""
    import subprocess
    import platform
    
    print(f"[FALLBACK] Using subprocess method")
    
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

    # Handle device selection
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
        
        # Configure startup info to hide console window
        startupinfo = None
        creationflags = 0
        
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            creationflags = subprocess.CREATE_NO_WINDOW
        
        # Run with real-time output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            startupinfo=startupinfo,
            creationflags=creationflags
        )
        
        # Print output in real-time
        for line in process.stdout:
            line = line.strip()
            if line:
                print(line)
        
        process.wait()
        
        if process.returncode == 0:
            print(f"\n✅ Separation completed successfully with {actual_device.upper()}!")
            return True
        else:
            print(f"\n⚠️  Separation completed with return code: {process.returncode}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during separation: {e}")
        return False

def main():
    input_file = sys.argv[1]
    stem_count = int(sys.argv[2])
    quality = sys.argv[3]
    audio_format = sys.argv[4]
    bitrate = sys.argv[5]
    requested_device = sys.argv[6]
    output_dir = sys.argv[7]
    
    print(f"\n{'='*50}")
    print(f"STEM SPLITTER - Processing: {os.path.basename(input_file)}")
    print(f"{'='*50}")
    
    # Try API first, fallback to subprocess if needed
    try:
        output_path = separate_with_api(
            input_file, stem_count, quality, audio_format, 
            bitrate, requested_device, output_dir
        )
        print(f"{'='*50}")
        
    except Exception as api_error:
        print(f"\n⚠️  API method failed: {api_error}")
        print("Attempting fallback to subprocess method...")
        print(f"{'='*50}")
        
        success = separate_with_subprocess(
            input_file, stem_count, quality, audio_format,
            bitrate, requested_device, output_dir
        )
        
        if not success:
            print(f"\n❌ Both separation methods failed.")
            sys.exit(1)

if __name__ == "__main__":
    main()