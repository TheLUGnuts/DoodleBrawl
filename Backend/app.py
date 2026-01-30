#jfr, cwf, tjc

from google import genai
from flask_cors import CORS
from dotenv import load_dotenv
from google.genai import types, errors
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

#################################
#          DOODLE BRAWL         #
#################################

load_dotenv()

app = Flask(__name__,
    static_folder="../Frontend/dist/assets",
    template_folder="../Frontend/dist",
    static_url_path="/assets")
#Cross Origin Resource Sharing prevention
app.config['SECRET_KEYS'] = os.getenv('SECRET_KEY')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

