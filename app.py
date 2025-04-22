from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import os
import webbrowser
import subprocess
import re

app = Flask(__name__)
CORS(app)

# Store chat history
chat_history = []

def is_command(message):
    # Check if message starts with common command prefixes
    command_prefixes = ['open', 'search', 'play', 'launch']
    return any(message.lower().startswith(prefix) for prefix in command_prefixes)

def execute_command(message):
    message = message.lower()
    
    if message.startswith('open'):
        # Extract the application/website name
        target = message[5:].strip()
        
        # Map common applications to their commands
        app_commands = {
            'youtube': 'https://www.youtube.com',
            'google': 'https://www.google.com',
            'github': 'https://www.github.com',
            'calculator': 'calc.exe',
            'notepad': 'notepad.exe',
            'chrome': 'chrome.exe',
            'firefox': 'firefox.exe',
            'edge': 'msedge.exe'
        }
        
        if target in app_commands:
            try:
                if app_commands[target].startswith('http'):
                    webbrowser.open(app_commands[target])
                    return f"Opening {target} in your default browser..."
                else:
                    subprocess.Popen(app_commands[target])
                    return f"Opening {target}..."
            except Exception as e:
                return f"Error opening {target}: {str(e)}"
        else:
            # Try to open as a website
            try:
                if not target.startswith(('http://', 'https://')):
                    target = 'https://' + target
                webbrowser.open(target)
                return f"Opening {target}..."
            except Exception as e:
                return f"Error opening {target}: {str(e)}"
    
    elif message.startswith('search'):
        # Extract the search query
        query = message[7:].strip()
        search_url = f"https://www.google.com/search?q={query}"
        webbrowser.open(search_url)
        return f"Searching for '{query}' on Google..."
    
    return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/send-message', methods=['POST'])
def send_message():
    global chat_history
    
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'response': 'Please enter a message.'})
    
    # Add user message to history
    chat_history.append({"role": "user", "content": user_message})
    
    try:
        # Check if it's a command
        command_response = execute_command(user_message)
        if command_response:
            chat_history.append({"role": "assistant", "content": command_response})
            return jsonify({'response': command_response})
        
        # If not a command, get response from Ollama
        response = requests.post(
            'http://localhost:11434/api/chat',
            json={
                "model": "tinyllama",
                "messages": chat_history,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            bot_response = response.json()['message']['content']
            # Add bot response to history
            chat_history.append({"role": "assistant", "content": bot_response})
            return jsonify({'response': bot_response})
        else:
            return jsonify({'response': 'Error: Could not get response from Ollama.'})
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'response': 'Sorry, I encountered an error. Please try again.'})

@app.route('/clear-history', methods=['POST'])
def clear_history():
    global chat_history
    chat_history = []
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True) 