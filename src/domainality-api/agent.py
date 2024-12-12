from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
import json
import traceback
import requests
import ast
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

provider_options =  {
          "model": "gpt-4o",
          "provider": "openai_chat",
          "moderateProvider": "openai",
          "moderatePrompt": True,
          "moderateTemplate": True,
          "max_tokens": 4096,
          "temperature": 0.7,
          "top_p": 1,
          "frequency_penalty": 0,
          "presence_penalty": 0,
        }


num_questions = 6

system_prompt = {"from": "system", 
        "content": """
Here are 10 dimensions  of domainalities.
1. Uniqueness and Memorability
Determines how important it is for the domain name to stand out and capture attention.
2. Brand Vibe
Explores the overall tone and personality of the brand or website.
3. Priority in Domain Features
Identifies what users prioritize most in a domain name.
4. TLD Alignment
Assesses preferences for top-level domains to match the brand's goals.
5. Keyword Style
Examines preferences for keyword types, such as abstract, industry-specific, action-oriented, or straightforward.
6. Audience Emotion
Focuses on the emotions users want their audience to feel when interacting with the domain name.
7. Domain Personality
Compares the domain name to a personality type.
8. Domain Length Flexibility
Measures the user's flexibility with domain length and the importance of brevity versus clarity.
9. Innovation vs. Tradition
Gauges whether users prefer a modern, innovative name or a more timeless, traditional one.
10. Non-Standard TLD Openness
Evaluates how open users are to less conventional TLDs and their willingness to experiment.

Please only return json message. You will keep asking questions to learn user preferences according to 10 dimensions  of domainalities, until user says 'start to give the final domain guessess'.
After user says 'start to give the final domain guessess', you will stop asking questions and then generate 5 recomended domains according to the preferences.
You need to figure out what 6/10 dimensions are most important, and what are the preferences for each of the 6 dimensions.
You need to include Domain Personality, TLD Alignment, Brand Vibe.
Questions should be only 1 sentence.
Do not include options text in the question. Try to keep the question as short as possible.
Each question should be given a scenario, please try not to ask in a direct way. For questions, given json format with question and 4 options {'chat': question, 'options': [options]}. 
Only after user request to give domain guessess
please start to give best 5 domain guessess rank from most recommended to lowest. For final guesses result, given in json format like 
{recommended_domains:{
   <remonmended domain names >:{
      "score":{
         "Uniqueness and Memorability":score,
         "Brand Vibe":score,
         ...
         "Non-Standard TLD Openness":score,
      },
      "price": usd_price
   }
}
}
"""}
ssojwt = os.getenv('SSO_JWT').strip()
headers = {
    "Authorization": f"sso-jwt {ssojwt}",
    "Content-Type": "application/json"
}

def run_thread(id):
    url = f"https://caas.api.godaddy.com/v1/threads/{id}/run"
    resp = requests.post(url, headers=headers, json=provider_options)

def get_messages(id):
    url = f"https://caas.api.godaddy.com/v1/threads/{id}"
    resp = requests.post(url, headers=headers)
    try:
        return resp.json()['data']['value']
    except Exception as e:
        # print(traceback.format_exc())
        print(resp.json())
        return 

def patch_conversation_gocass(msg, role, id):
    if id:
        data = {
        "messages": [
                {
                "from": role,
                "content": msg,
                }
            ]
            }
        url = f"https://caas.api.godaddy.com/v1/threads/{id}"
        resp = requests.patch(url, headers=headers, json=data)
        # print(resp)
        print('calling run thread')
        return id
    else:
        url = "https://caas.api.godaddy.com/v1/threads"
        data = {
                "name": "Domainality",
                "description": "customer thread",
                "messages": [
                    system_prompt,
                    {
                        "from": role,
                        "content":msg
                    }
                ],
                "provider": "openai_chat",
                "providerOptions": provider_options
                }
        response = requests.post(url, headers=headers, json=data)
        print(response.json())
        id = response.json()['data']['id']
        return id

def delete_thread(id):
    url = f"https://caas.api.godaddy.com/v1/threads/{id}"
    resp = requests.delete(url, headers=headers)
    # print(resp)


# Define the home route
@app.route("/")
def home():
    return render_template("index.html")

# Define the chat route
@app.route("/chat", methods=["POST"])
def chat():
    is_last = False
    # Retrieve the user's input and previous conversation from session
    user_input = request.json.get("message")
    user_text = request.json.get("textInput")
    thread_id = session.get("thread_id")
    delete_thread_flag = False
    cnt = session.get("cnt", 1)
    print(cnt)
    thread_id = patch_conversation_gocass(user_input, 'user', thread_id)
    if user_text:
        print('user text', user_text)
        thread_id = patch_conversation_gocass(user_text, 'user', thread_id)
        thread_id = patch_conversation_gocass('start to give the final domain guessess', 'user', thread_id)
        delete_thread_flag = True
    run_thread(thread_id)
    session["thread_id"] = thread_id
    response = get_messages(thread_id)
    # print(response)
    if cnt == num_questions:
        is_last = True
    cnt += 1
    session["cnt"] = cnt     
    res = {
        'content': ast.literal_eval(response.get("content").replace('```json','').replace('```','')),
        'isLast': is_last
        }
    if delete_thread_flag:
        delete_thread(thread_id)
        session['thread_id'] = None
        session['cnt'] = 0
        print('deleting thread')
    print(res)
    return res

# Define a route to reset the conversation
@app.route("/reset", methods=["POST"])
def reset_conversation():
    session.pop("thread_id", None)
    session.pop("cnt", None)
    return jsonify({"message": "Conversation reset successfully!"})

if __name__ == "__main__":
    app.run(debug=True)
