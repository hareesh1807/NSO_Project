import flask
import time
import socket

h_name = socket.gethostname()
IP_addres = socket.gethostbyname(h_name)

app = flask.Flask(__name__)

@app.route('/')
def index():
    Time = time.strftime("%H:%M:%S")
    return Time + " Serving from " + h_name + " (" + IP_addres + ")\n"

# Ansible uses this to check if the app is alive!
@app.route('/health')
def health():
    return "OK", 200

# The engine that actually turns the server on
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)