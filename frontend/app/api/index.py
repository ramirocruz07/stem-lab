from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
import torch
from demucs import pretrained
from demucs.apply import apply_model
from demucs.audio import AudioFile, save_audio

app = Flask(__name__)
CORS(app)

# Load model once
model = pretrained.get_model('htdemucs')
model.eval()

@app.route('/api/separate', methods=['POST'])
def separate_audio():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            audio_file.save(tmp_file.name)
            input_path = tmp_file.name
        
        # Process with Demucs
        stems = separate_with_demucs(input_path)
        
        # Cleanup
        os.unlink(input_path)
        
        return jsonify({
            'status': 'success',
            'stems': stems
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def separate_with_demucs(audio_path):
    """Separate audio using Demucs (no torchaudio needed)"""
    
    # Load audio using Demucs' built-in AudioFile
    audio = AudioFile(audio_path).read(streams=0)
    audio = audio.mean(dim=0)  # Convert to mono if needed
    
    # Separate stems
    with torch.no_grad():
        sources = apply_model(model, audio[None], device='cpu')[0]
    
    stems = []
    stem_names = ['vocals', 'drums', 'bass', 'other']
    
    # Save each stem temporarily
    for i, name in enumerate(stem_names):
        stem_audio = sources[i]
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
            save_audio(stem_audio, tmp.name, 44100)
            
            # Read file content
            with open(tmp.name, 'rb') as f:
                audio_data = f.read()
            
            os.unlink(tmp.name)  # Cleanup
        
        stems.append({
            'name': name,
            'data': audio_data.hex(),  # Convert to hex for JSON
            'size': len(audio_data)
        })
    
    return stems