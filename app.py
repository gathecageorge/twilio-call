import os
from flask import Flask, request, Response, url_for
from twilio.rest import Client
import json
import redis

users = os.environ["ESCALATE_USERS"]
app = Flask(__name__)
r = redis.Redis(host='redis-alpine', port=6379, db=0)

def save_data(key, value):
    r.set(key, value)
    print(f"Data saved: {key} -> {value}")

def retrieve_data(key):
    return r.get(key)

@app.route("/")
def index():
    version = os.environ["APP_VERSION"]
    return f"<h1>This is Twilio app version: {version}!</h1>"

@app.route('/get/<key>', methods=['GET'])
def get_value(key):
  json_data = json.loads(retrieve_data(key))

  say_text = f"<Say voice=\"woman\">Escalation for {json_data['alert_payload']['commonLabels']['alertname']} alert. There are {json_data['alert_payload']['numFiring']} alerts in firing state.</Say>"

  index = 1
  for alert in json_data['alert_payload']['alerts']:
     say_text += f"<Pause length=\"1\"/><Say voice=\"woman\">Alert {index} summary: {alert['annotations']['summary']}. </Say>"
     index += 1

  xml_data = f'<Response>{say_text}</Response>'

  return Response(xml_data, mimetype='text/xml')

@app.route('/make-call', methods=['POST'])
def make_call():
  account_sid = os.environ["TWILIO_ACCOUNT_SID"]
  auth_token = os.environ["TWILIO_AUTH_TOKEN"]
  client = Client(account_sid, auth_token)

  json_data = request.json
  id = json_data['alert_group_id']
  formatted_json = json.dumps(json_data, indent=4, sort_keys=True)
  save_data(id, formatted_json)

  say_url = url_for('get_value', key=id, _external=True)

  call = client.calls.create(
    url = say_url,
    to = users,
    from_ = os.environ["FROM_NUMBER"]
  )

  return (call.sid)

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5051, debug=True)
  # from waitress import serve
  # serve(app, host="0.0.0.0", port=5051)
