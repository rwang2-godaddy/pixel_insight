from flask import Flask, render_template, request, jsonify, session
import os
import json
import boto3
import traceback  # Add this line
from botocore.exceptions import NoCredentialsError, PartialCredentialsError  # Import the required exceptions
import base64
import requests
from werkzeug.utils import secure_filename
from services.gocaas_client import GoCaaS
from services.prompts import PROMPTS
from authentications.jwt_token_client import get_jwt_token
from flask_cors import CORS  # Import CORS
import ast
# from common.utils import process_conversation_gocass, run_thread, get_messages, delete_thread
# import ast
# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management

# Initialize AWS Rekognition client
rekognition_client = boto3.client('rekognition', region_name='us-east-1')

CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://localhost:3000"}})
app.config['UPLOAD_FOLDER'] = './uploads'
AVAILCHECK_URL = 'https://availcheck.api.dev.aws.godaddy.com/v4/domains/available'
USE_AC_OPTIMIZATION = True

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

def encode_image(image_path):
    """Encode an image file to a base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def availcheck(sld_list):
    """Check domain availability for given SLDs."""
    domain_list = [f"{sld}{tld}" for sld in sld_list for tld in ['.com', '.net', '.org']]
    post_json_content = {"domains": domain_list}
    headers = {'X-App-Key': 'test_missspell'}
    params = {'optimization': 'FAST'} if USE_AC_OPTIMIZATION else {}
    
    response = requests.post(AVAILCHECK_URL, params=params, json=post_json_content, headers=headers)
    response.raise_for_status()  # Raise an exception for HTTP errors
    json_response = response.json()

    return [{'domain': d['domain'], 'is_available': d['available']} for d in json_response['domains']]


@app.route('/analyze-image', methods=['POST'])
async def analyze_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files['image']

    try:
        # Convert the image to bytes
        image_bytes = image_file.read()

        # Call Rekognition to analyze the image
        response = rekognition_client.detect_labels(
            Image={'Bytes': image_bytes},
            MaxLabels=10,
            MinConfidence=75
        )
        print(response)
        # Extract labels and confidence from response
        labels = [
            {"Name": label['Name'], "Confidence": label['Confidence']}
            for label in response.get('Labels', [])
        ]
        print(labels)
        llm = GoCaaS("gpt-4o", token=get_jwt_token().token)
        llm_response = await llm.call(f"""
        here are a list of keywords of an image: {labels}, please generate 5 creative, brandable domain names related to the image provided.                         
        """, [])
        print(llm_response['data']['value'])
        return jsonify({"labels": labels}), 200
    except NoCredentialsError:
        return jsonify({"error": "AWS credentials not found"}), 500
    except PartialCredentialsError:
        return jsonify({"error": "Incomplete AWS credentials"}), 500
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    
@app.route('/image', methods=['POST'])
async def image():
    print(request)
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    # Handle uploaded image
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    # Save file securely
    labels = session.get("labels", [])
    if len(labels) == 0:
        image_file = request.files['image']
        image_bytes = image_file.read()
        response = rekognition_client.detect_labels(
                Image={'Bytes': image_bytes},
                MaxLabels=10,
                MinConfidence=75
        )
            # Extract labels and confidence from response
        labels = [
            {"Name": label['Name'], "Confidence": label['Confidence']}
            for label in response.get('Labels', [])
        ]
        session['labels']=labels

    try:
        # Initialize LLM service
        llm = GoCaaS("gpt-4o", token=get_jwt_token().token)
            # Interactive mode
        conversation_history = session.get("conversation", [])
        if prompt_index <= 3:
            session['prompt'] = prompt_index + 1
            user_input = request.args.get("message", "")
            if user_input in ["a", "b", "c", "d"]:
                 conversation_history.append({"role": "user", "content": f"I'm choosing option {user_input} for the {prompt_index-1}th question."})
                 conversation_history.append({
                     "role": "user",
                     "content": PROMPTS[prompt_index]['prompt']
                 })
                 response = await llm.call(conversation_history[-1]["content"], conversation_history)
            else:
                conversation_history.append({
                    "role": "user",
                    "content": PROMPTS[prompt_index]['prompt']
                })
                response = await llm.call(conversation_history[-1]["content"], conversation_history)

            assistant_reply = response["data"]["value"]
            conversation_history.append({"role": "assistant", "content": assistant_reply})
            session["conversation"] = conversation_history
            try:
                assistant_reply = response["data"]["value"].replace("```json", "").replace("```", "")
                return {
                    'success': True,
                    'prompt_id': prompt_index,
                    'content': ast.literal_eval(assistant_reply),
                }
            except Exception as e:
                print(traceback.format_exc())
        elif prompt_index ==4:
            conversation_history.append({
                    "role": "user",
                    "content": f"Based on the answer provided, generate a 5 creative, brandable domain names for a website related to the keywords {session['labels']} provided." + 
                    PROMPTS[prompt_index]['prompt']
                })
            response = await llm.call(conversation_history[-1]["content"], conversation_history)
            assistant_reply = response["data"]["value"].replace("```json", "").replace("```", "")
            
            return {
                'success': True,
                'prompt_id': prompt_index,
                'content': ast.literal_eval(assistant_reply),
            }
        
        else:
             session.pop("prompt", None)
             session.pop("conversation", None)
             session.pop("labels", None)
             return jsonify({
                 'success': True,
                 'prompt_id': prompt_index,
                 'chat_response': "conversation reset successfully",
             }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
    finally:
        pass






if __name__ == '__main__':
    app.run(debug=True, port=5001)