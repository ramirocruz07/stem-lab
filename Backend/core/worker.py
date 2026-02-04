import os
import sys
import subprocess
import re
import time
import platform
from PyQt6.QtCore import QThread, pyqtSignal

class SplitterWorker(QThread):
    finished = pyqtSignal()
    progress_changed = pyqtSignal(int)
    output_ready = pyqtSignal(str)
    gpu_memory_update = pyqtSignal(str)  # New signal for GPU memory updates
    current_file = pyqtSignal(str)
    error_occurred = pyqtSignal(str)  # Signal for error messages

    def __init__(self, file, stems, quality, audio_format, bitrate, device, output_dir):
        super().__init__()
        self.file = file
        self.stems = stems
        self.audio_format = audio_format
        self.quality = quality
        self.device = device
        self.output_dir = output_dir
        self.bitrate = bitrate
        self.last_progress = 0
        self.running = True
        self.process = None
        self._cancel_requested = False

    def run(self):
        try:
            # Start GPU memory monitoring only when running on GPU
            if self.device == "cuda":
                self.start_gpu_monitor()
            
            print(f"\n[START] Starting separation: {os.path.basename(self.file)}")
            print(f"[INFO] Settings: {self.stems} stems, {self.quality} quality, {self.audio_format} format, Device: {self.device}")
            filename = os.path.basename(self.file)
            self.current_file.emit(filename)
            
            # Handle frozen executable (PyInstaller) vs normal Python execution
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                # When frozen, we can't easily run separator.py as subprocess
                # Instead, import and run it directly, capturing stdout
                try:
                    from core import separator
                    
                    # Custom stdout class to capture output
                    class OutputCapture:
                        """
                        Lightweight stdout replacement used when running under PyInstaller.
                        NOTE: In a windowed build sys.stdout/sys.__stdout__ can be None,
                        so all writes to the "real" stdout must be optional.
                        """

                        def __init__(self, worker):
                            self.worker = worker
                            self.buffer = ""
                            # Prefer the real console stdout if it exists, otherwise None
                            self.original_stdout = getattr(sys, "__stdout__", None) or getattr(sys, "stdout", None)
                        
                        def write(self, text):
                            # Best‑effort write to original stdout (if any)
                            if self.original_stdout is not None:
                                try:
                                    self.original_stdout.write(text)
                                    self.original_stdout.flush()
                                except Exception:
                                    # Never crash the app if console writing fails
                                    pass
                            
                            # Add to buffer and process lines for progress/output parsing
                            self.buffer += text
                            while '\n' in self.buffer or '\r' in self.buffer:
                                if '\n' in self.buffer:
                                    line, self.buffer = self.buffer.split('\n', 1)
                                elif '\r' in self.buffer:
                                    line, self.buffer = self.buffer.split('\r', 1)
                                else:
                                    break
                                
                                line = line.strip()
                                if not line:
                                    continue
                                
                                # Progress parsing
                                percent = self.worker.extract_percentage(line)
                                if percent is not None and percent > self.worker.last_progress:
                                    self.worker.progress_changed.emit(percent)
                                    self.worker.last_progress = percent
                                
                                # Output folder detection
                                if 'writing to' in line.lower() or 'saved to' in line.lower():
                                    folder_match = re.search(
                                        r'writing to (.+)|saved to (.+)',
                                        line,
                                        re.IGNORECASE
                                    )
                                    if folder_match:
                                        folder_path = folder_match.group(1) or folder_match.group(2)
                                        if folder_path and os.path.exists(folder_path):
                                            self.worker.output_ready.emit(folder_path)
                        
                        def flush(self):
                            if self.original_stdout is not None:
                                try:
                                    self.original_stdout.flush()
                                except Exception:
                                    pass
                    
                    # Set up sys.argv and redirect stdout
                    original_argv = sys.argv[:]
                    sys.argv = [
                        'separator.py',
                        self.file,
                        str(self.stems),
                        self.quality,
                        self.audio_format,
                        self.bitrate,
                        self.device,
                        self.output_dir
                    ]
                    
                    # Capture stdout
                    capture = OutputCapture(self)
                    sys.stdout = capture
                    
                    try:
                        # Run separator.main()
                        separator.main()
                    finally:
                        # Restore stdout and argv
                        sys.stdout = capture.original_stdout
                        sys.argv = original_argv
                    
                    # Emit final progress
                    if not self._cancel_requested and self.last_progress < 100:
                        self.progress_changed.emit(100)
                    
                    # Final output folder fallback
                    if not self._cancel_requested:
                        output_folder = self.get_output_folder()
                        if output_folder:
                            self.output_ready.emit(output_folder)
                    
                    self.running = False
                    self.finished.emit()
                    return
                    
                except Exception as e:
                    error_msg = f"Error running separator: {str(e)}"
                    print(f"[ERROR] Error running separator directly: {e}")
                    import traceback
                    traceback.print_exc()
                    # In frozen mode, don't fall back to subprocess as it would spawn another exe
                    # Just emit error and finish
                    self.running = False
                    self.error_occurred.emit(error_msg)
                    self.finished.emit()
                    return
            else:
                # Normal Python execution - use subprocess
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                separator_path = os.path.join(base_dir, "core", "separator.py")
                
                # Check if separator.py exists
                if not os.path.exists(separator_path):
                    error_msg = f"Separator script not found at: {separator_path}"
                    print(f"[ERROR] {error_msg}")
                    self.error_occurred.emit(error_msg)
                    self.running = False
                    self.finished.emit()
                    return

                cmd = [
                    sys.executable,
                    "-u", 
                    separator_path,
                    self.file,
                    str(self.stems),
                    self.quality,
                    self.audio_format,
                    self.bitrate,
                    self.device,
                    self.output_dir
                ]
            
            # Create subprocess to run separator (only if not already returned)
            # Prevent console window from appearing on Windows
            creation_flags = 0
            if platform.system() == "Windows":
                creation_flags = subprocess.CREATE_NO_WINDOW
            
            try:
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    creationflags=creation_flags
                )
            except FileNotFoundError as e:
                error_msg = f"Failed to start process: {str(e)}\n\nPlease ensure Python is properly installed and accessible."
                print(f"[ERROR] {error_msg}")
                self.error_occurred.emit(error_msg)
                self.running = False
                self.finished.emit()
                return
            except Exception as e:
                error_msg = f"Failed to start subprocess: {str(e)}"
                print(f"[ERROR] {error_msg}")
                self.error_occurred.emit(error_msg)
                self.running = False
                self.finished.emit()
                return

            buffer = ""
            process_ended = False

            while True:
                # ✅ Cancel support
                if self._cancel_requested:
                    break

                # Check if process has ended
                poll_result = self.process.poll()
                if poll_result is not None:
                    process_ended = True
                    # Read any remaining output
                    try:
                        remaining = self.process.stdout.read()
                        if remaining:
                            buffer += remaining
                            # Process remaining buffer
                            for line in buffer.splitlines():
                                line = line.strip()
                                if not line:
                                    continue
                                print(f"[OUTPUT] {line}")  # Debug output
                                # Progress parsing
                                percent = self.extract_percentage(line)
                                if percent is not None and percent > self.last_progress:
                                    self.progress_changed.emit(percent)
                                    self.last_progress = percent
                                # Output folder detection
                                if 'writing to' in line.lower() or 'saved to' in line.lower():
                                    folder_match = re.search(
                                        r'writing to (.+)|saved to (.+)',
                                        line,
                                        re.IGNORECASE
                                    )
                                    if folder_match:
                                        folder_path = folder_match.group(1) or folder_match.group(2)
                                        if folder_path and os.path.exists(folder_path):
                                            self.output_ready.emit(folder_path)
                    except Exception as e:
                        print(f"[WARNING] Error reading remaining output: {e}")
                    break

                try:
                    char = self.process.stdout.read(1)
                    if not char:
                        # No more data available right now
                        # Check if process ended
                        if self.process.poll() is not None:
                            process_ended = True
                            break
                        # Small delay to avoid busy waiting
                        time.sleep(0.05)
                        continue

                    if char in ("\r", "\n"):
                        line = buffer.strip()
                        buffer = ""

                        if not line:
                            continue

                        print(f"[OUTPUT] {line}")  # Debug output
                        # Progress parsing
                        percent = self.extract_percentage(line)
                        if percent is not None and percent > self.last_progress:
                            self.progress_changed.emit(percent)
                            self.last_progress = percent

                        # Output folder detection
                        if 'writing to' in line.lower() or 'saved to' in line.lower():
                            folder_match = re.search(
                                r'writing to (.+)|saved to (.+)',
                                line,
                                re.IGNORECASE
                            )
                            if folder_match:
                                folder_path = folder_match.group(1) or folder_match.group(2)
                                if folder_path and os.path.exists(folder_path):
                                    self.output_ready.emit(folder_path)

                    else:
                        buffer += char
                except Exception as e:
                    print(f"[WARNING] Error reading process output: {e}")
                    # Check if process ended
                    if self.process.poll() is not None:
                        process_ended = True
                        break
                    time.sleep(0.1)

            # Process ended or cancelled
            return_code = self.process.wait() if not process_ended else self.process.returncode
            self.running = False

            # Check if process failed
            if return_code != 0 and not self._cancel_requested:
                # If process exited immediately with error, try to get error message from stderr or output
                error_details = ""
                try:
                    # Try to read any error output
                    if hasattr(self.process, 'stderr') and self.process.stderr:
                        error_output = self.process.stderr.read()
                        if error_output:
                            error_details = f"\n\nError details: {error_output[:500]}"  # Limit length
                except:
                    pass
                
                if self.last_progress == 0:
                    # Process failed immediately - likely demucs not found or invalid command
                    error_msg = (
                        f"Processing failed immediately (return code {return_code}).\n\n"
                        f"This usually means:\n"
                        f"- 'demucs' command is not installed or not in PATH\n"
                        f"- The input file is invalid or inaccessible\n"
                        f"- Required dependencies are missing\n\n"
                        f"Please check the console output for more details.{error_details}"
                    )
                else:
                    # Process started but failed later
                    error_msg = (
                        f"Processing failed with return code {return_code}.\n\n"
                        f"Progress reached: {self.last_progress}%\n"
                        f"Please check the console output for more details.{error_details}"
                    )
                
                print(f"[ERROR] {error_msg}")
                self.error_occurred.emit(error_msg)
                self.finished.emit()
                return

            # Emit final progress only if not cancelled
            if not self._cancel_requested and self.last_progress < 100:
                self.progress_changed.emit(100)

            # Final output folder fallback
            if not self._cancel_requested:
                output_folder = self.get_output_folder()
                if output_folder:
                    self.output_ready.emit(output_folder)

            self.running = False
            self.finished.emit()
            
        except Exception as e:
            # Catch any errors to prevent app crash
            error_msg = f"Error during processing: {str(e)}"
            print(f"[ERROR] Error in worker.run(): {e}")
            import traceback
            traceback.print_exc()
            self.running = False
            # Emit error signal so UI can show it to user
            self.error_occurred.emit(error_msg)
            # Still emit finished so UI can recover
            self.finished.emit()
    
    def start_gpu_monitor(self):
        """Start monitoring GPU memory usage in a separate thread using nvidia-smi.

        This reads real GPU usage from the system, so it also sees memory used
        by the Demucs subprocess (not just this Python process).
        """
        import threading
        import subprocess as sp

        def monitor_gpu():
            while self.running and not self._cancel_requested:
                try:
                    # Query used/total memory (in MB) for GPU 0
                    result = sp.run(
                        ["nvidia-smi",
                         "--query-gpu=memory.used,memory.total",
                         "--format=csv,nounits,noheader"],
                        capture_output=True,
                        text=True,
                        timeout=1,
                    )
                    if result.returncode == 0:
                        line = result.stdout.strip().splitlines()[0]
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) == 2:
                            used_mb = float(parts[0])
                            total_mb = float(parts[1])
                            used_gb = used_mb / 1024.0
                            total_gb = total_mb / 1024.0
                            memory_text = f"GPU Memory: {used_gb:.2f}/{total_gb:.2f} GB"
                            self.gpu_memory_update.emit(memory_text)
                except (FileNotFoundError, sp.TimeoutExpired, ValueError, IndexError):
                    # nvidia-smi not available or output unexpected; just stop trying
                    break
                except Exception:
                    # Any other unexpected error: don't crash the app, just stop updates
                    break

                time.sleep(1.5)  # Update roughly every 1.5 seconds

        monitor_thread = threading.Thread(target=monitor_gpu, daemon=True)
        monitor_thread.start()
    
    def extract_percentage(self, line):
        """Extract percentage from various Demucs output formats"""
        try:
            # Format 1: "14%|########2 | 23.4/169.65"
            if '|' in line and '%' in line:
                parts = line.split('|')
                if parts and '%' in parts[0]:
                    percent_str = parts[0].replace('%', '').strip()
                    return int(percent_str)
            
            # Format 2: Just "14%" at the beginning
            if line.startswith(('0%', '1%', '2%', '3%', '4%', '5%', '6%', '7%', '8%', '9%')):
                percent_str = line.split('%')[0].strip()
                return int(percent_str)
            
            # Format 3: Contains " X% " somewhere
            match = re.search(r'(\d+)%', line)
            if match:
                return int(match.group(1))
                
        except (ValueError, IndexError):
            pass
        
        return None
    
    def cancel(self):
        self._cancel_requested = True

        if self.process:
            try:
                self.process.terminate()  # graceful stop
            except Exception:
                pass

    def get_output_folder(self):
        """Get the actual output folder where stems are saved"""
        import os
        from pathlib import Path
        
        # Determine model name based on stem count
        model_name = "htdemucs"
        if self.stems == 2:
            model_name = "htdemucs_ft"
        elif self.stems == 6:
            model_name = "htdemucs_6s"
        
        # Get input file name without extension
        input_name = Path(self.file).stem
        
        # Try multiple possible output locations
        
        # 1. User-specified output directory
        if self.output_dir:
            output_folder = os.path.join(self.output_dir, model_name, input_name)
            if os.path.exists(output_folder):
                return output_folder
        
        # 2. Demucs default locations
        default_locations = [
            os.path.join(os.path.expanduser("~"), "separated"),
            os.path.join(os.path.expanduser("~"), "Downloads", "Demucs"),
            os.path.join(os.path.expanduser("~"), "Desktop", "Demucs"),
            os.path.join(os.path.expanduser("~"), "Documents", "Demucs"),
            os.path.join(os.getcwd(), "separated"),
        ]
        
        for base_output in default_locations:
            output_folder = os.path.join(base_output, model_name, input_name)
            if os.path.exists(output_folder):
                return output_folder
        
        return None