


from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = '../../uploads'  # relative to index.py
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploadaudio', methods=['POST'])
def upload_audio():
   print("im here")
   uploaded_file = request.files.get('my-file')
   if not uploaded_file:
        return jsonify({'message': 'No file received'}), 400

   if uploaded_file.filename == '' or not allowed_file(uploaded_file.filename):
     return jsonify({'message': 'Invalid file type'}), 400
   print("im here 2")
   filename = secure_filename(uploaded_file.filename)
   print(filename)
   uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
   return jsonify({'message': 'File uploaded successfully'}), 200
   
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5328, debug=True)


# import os
# import tempfile
# import boto3
# from io import BytesIO
# from flask import Flask, request, jsonify
# import torch
# import torchaudio
# from demucs import pretrained
# from demucs.apply import apply_model

# app = Flask(__name__)

# # Initialize models (this runs once when function starts)
# def load_model(model_name):
#     if model_name == 'demucs':
#         return pretrained.get_model('htdemucs')
#     elif model_name == 'spleeter':
#         # Spleeter equivalent
#         from spleeter.separator import Separator
#         return Separator('spleeter:4stems')
#     else:
#         # Open Unmix
#         import openunmix
#         return openunmix.umxl()

# @app.route('/api/separate', methods=['POST'])
# def separate_audio():
#     try:
#         if 'audio' not in request.files:
#             return jsonify({'error': 'No audio file provided'}), 400
        
#         audio_file = request.files['audio']
#         model_name = request.form.get('model', 'demucs')
        
#         # Validate file size (max 10MB)
#         audio_file.seek(0, os.SEEK_END)
#         file_size = audio_file.tell()
#         audio_file.seek(0)
        
#         if file_size > 10 * 1024 * 1024:  # 10MB
#             return jsonify({'error': 'File too large (max 10MB)'}), 400
        
#         # Process audio
#         with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
#             audio_file.save(tmp_file.name)
#             stems = separate_stems(tmp_file.name, model_name)
            
#         # Clean up
#         os.unlink(tmp_file.name)
        
#         return jsonify({
#             'status': 'success',
#             'stems': stems
#         })
        
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# def separate_stems(audio_path, model_name):
#     """Separate audio using specified model"""
    
#     if model_name == 'demucs':
#         return separate_with_demucs(audio_path)
#     elif model_name == 'spleeter':
#         return separate_with_spleeter(audio_path)
#     else:
#         return separate_with_openunmix(audio_path)

# def separate_with_demucs(audio_path):
#     """Separate using Demucs (highest quality)"""
#     model = pretrained.get_model('htdemucs')
#     model.eval()
    
#     # Load and process audio
#     wav, sr = torchaudio.load(audio_path)
#     if wav.shape[0] > 1:
#         wav = wav.mean(dim=0, keepdim=True)  # to mono
    
#     # Resample if needed
#     if sr != 44100:
#         wav = torchaudio.functional.resample(wav, sr, 44100)
    
#     # Separate stems
#     with torch.no_grad():
#         sources = apply_model(model, wav[None], device='cpu')[0]
    
#     stems = []
#     stem_names = ['vocals', 'drums', 'bass', 'other']
    
#     for i, name in enumerate(stem_names):
#         stem_audio = sources[i]
        
#         # Convert to bytes
#         buffer = BytesIO()
#         torchaudio.save(buffer, stem_audio.unsqueeze(0), 44100, format='wav')
#         buffer.seek(0)
        
#         stems.append({
#             'name': name,
#             'audio_data': buffer.getvalue(),
#             'content_type': 'audio/wav'
#         })
    
#     return stems

# def separate_with_spleeter(audio_path):
#     """Separate using Spleeter (fastest)"""
#     from spleeter.separator import Separator
    
#     separator = Separator('spleeter:4stems')
#     separator.separate_to_file(audio_path, './output')
    
#     stems = []
#     stem_names = ['vocals', 'drums', 'bass', 'other']
    
#     for name in stem_names:
#         output_path = f'./output/{os.path.basename(audio_path)}/{name}.wav'
#         with open(output_path, 'rb') as f:
#             stems.append({
#                 'name': name,
#                 'audio_data': f.read(),
#                 'content_type': 'audio/wav'
#             })
    
#     return stems

# # Similar functions for Open Unmix...