from flask import Flask, request, jsonify
import os
from openai import OpenAI
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile
import time

load_dotenv()

app = Flask(__name__)
CORS(app)

api_key = os.getenv('API_KEY')
assistant_id = os.getenv('ASSISTANT_ID')

client = OpenAI(api_key=api_key)

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.form.get('question', '')
    image_file = request.files.get('image', None)

    if image_file:
        temp_path = os.path.join(tempfile.gettempdir(), secure_filename(image_file.filename))
        image_file.save(temp_path)
        file = client.files.create(file=open(temp_path, "rb"), purpose="vision")

        messages = [{
            "role": "user",
            "content": [
                {
                    "type": "image_file",
                    "image_file": {"file_id": file.id}
                }
            ]
        }]
    else:
        messages = [{
            "role": "user",
            "content": user_input
        }]

    thread = client.beta.threads.create(messages=messages)
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)

    while run.status != "completed":
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        time.sleep(1)

    message_response = client.beta.threads.messages.list(thread_id=thread.id)
    info_text = "No information found."

    for message in message_response.data:
        for content in message.content:
            print("\ncontent >>>", content)
            # Исправленный доступ к данным в TextContentBlock
            if content.type == 'text':
                info_text = content.text.value
                break
        if info_text != "No information found.":
            break  # Если найдена информация, выходим из внешнего цикла

    return jsonify({"response": info_text})

if __name__ == '__main__':
    app.run(debug=True)
