import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join('/tmp', file.filename)
    file.save(file_path)

    transcription = transcribe_audio(file_path)
    return jsonify({"transcription": transcription})

def transcribe_audio(file_path):
    api_key = os.getenv('AAI_API')  # Ensure this environment variable is set with your AssemblyAI API key
    headers = {'authorization': api_key}
    with open(file_path, 'rb') as f:
        response = requests.post('https://api.assemblyai.com/v2/upload', headers=headers, files={'file': f})
    upload_url = response.json()['upload_url']

    response = requests.post('https://api.assemblyai.com/v2/transcript', headers=headers, json={'audio_url': upload_url})
    transcript_id = response.json()['id']

    while True:
        response = requests.get(f'https://api.assemblyai.com/v2/transcript/{transcript_id}', headers=headers)
        result = response.json()
        if result['status'] == 'completed':
            return result['text']
        elif result['status'] == 'failed':
            return 'Transcription failed'

if __name__ == '__main__':
    app.run(debug=True)