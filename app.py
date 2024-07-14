import os
from flask import Flask, request, jsonify
from twilio.rest import Client
import datetime
import json

app = Flask(__name__)

@app.route("/")
def index():
    version = os.environ["APP_VERSION"]
    return f"<h1>This is Twilio app version: {version}!</h1>"

@app.route('/make-call', methods=['POST'])
def make_call():
  account_sid = os.environ["TWILIO_ACCOUNT_SID"]
  auth_token = os.environ["TWILIO_AUTH_TOKEN"]
  client = Client(account_sid, auth_token)

  current_datetime = datetime.datetime.now()
  file_name = f"/data/file_{current_datetime.strftime('%Y-%m-%d-%H:%M:%S')}.txt"
  f = open(file_name, "a")
  f.write(json.dumps(request.json, indent=4, sort_keys=True))
  f.close()
  return request.json

  # call = client.calls.create(
  #   url = "http://demo.twilio.com/docs/voice.xml",
  #   to = "+351914077402",
  #   from_ = os.environ["FROM_NUMBER"]
  # )

  # return (call.sid)

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5051, debug=True)
  # from waitress import serve
  # serve(app, host="0.0.0.0", port=5051)
