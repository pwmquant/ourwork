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
    print(f"File saved to {file_path}")

    transcription = transcribe_audio(file_path)
    return jsonify({"transcription": transcription})

def transcribe_audio(file_path):
    api_key = os.getenv('AAI_API')  # Ensure this environment variable is set with your AssemblyAI API key
    if not api_key:
        print("AssemblyAI API key is not set")
        return "API key not set"

    headers = {'authorization': api_key}
    with open(file_path, 'rb') as f:
        response = requests.post('https://api.assemblyai.com/v2/upload', headers=headers, files={'file': f})
    
    if response.status_code != 200:
        print(f"Error uploading file: {response.json()}")
        return "Error uploading file"

    upload_url = response.json().get('upload_url')
    if not upload_url:
        print("Failed to get upload URL")
        return "Failed to get upload URL"

    response = requests.post('https://api.assemblyai.com/v2/transcript', headers=headers, json={'audio_url': upload_url})
    if response.status_code != 200:
        print(f"Error starting transcription: {response.json()}")
        return "Error starting transcription"
    
    transcript_id = response.json().get('id')
    if not transcript_id:
        print("Failed to get transcript ID")
        return "Failed to get transcript ID"

    while True:
        response = requests.get(f'https://api.assemblyai.com/v2/transcript/{transcript_id}', headers=headers)
        result = response.json()
        if result['status'] == 'completed':
            return result['text']
        elif result['status'] == 'failed':
            print("Transcription failed")
            return 'Transcription failed'
        elif result['status'] == 'queued':
            continue
        else:
            print(f"Unexpected status: {result['status']}")
            continue

if __name__ == '__main__':
    app.run(debug=True)
