import os
from flask import Flask, request, Response
from twilio.rest import Client
import json
import redis
import time
import threading

account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
users = json.loads(os.environ["ESCALATE_USERS"])

app = Flask(__name__)
r = redis.Redis(host='redis-alpine', port=6379, db=0)

def save_data(key, value, expiration=3600):
    r.setex(key, expiration, value)
    print(f"Data saved: {key} -> {value}")

def retrieve_data(key):
    return r.get(key)

def getUserMobile(users_to_be_notified, index):
  username = users_to_be_notified[index % len(users_to_be_notified)]['username']
  return {
     "mobile": users[username],
     "username": username
  }

@app.route("/")
def index():
    version = os.environ["APP_VERSION"]
    return f"<h1>This is Twilio app version: {version}!</h1>"

@app.route('/get/<key>', methods=['POST', 'GET'])
def get_value(key):
  data = retrieve_data(key)
  if data == None:
     return Response(f"<Response><Say voice=\"woman\">There was an error retrieving information for alert ID {key}, check on slack as soon as possible to resolve.</Say></Response>", mimetype='text/xml')

  json_data = json.loads(data)
  say_text = f"<Say voice=\"woman\">Hello {json_data['current_person']['username']}, Escalation for {json_data['alert_payload']['commonLabels']['alertname']} alert. There are {json_data['alert_payload']['numFiring']} alerts in firing state.</Say>"

  index = 1
  for alert in json_data['alert_payload']['alerts']:
     say_text += f"<Pause length=\"1\"/><Say voice=\"woman\">Alert {index} summary: {alert['annotations']['summary']}. </Say>"
     index += 1

  xml_data = f'<Response>{say_text}</Response>'

  return Response(xml_data, mimetype='text/xml')

@app.route('/call-update/<key>', methods=['POST'])
def call_update(key):
  data = retrieve_data(key)
  if data == None:
     return f"There was an error retrieving information for alert ID {key}, check on slack as soon as possible to resolve"

  json_data = json.loads(data)
  retry = json_data['next_retry']

  twilio_response = request.form
  json_data['next_retry'] = retry + 1
  json_data['last_twilio_response'] = twilio_response

  if twilio_response['CallStatus'] != 'completed' and retry < 5:
    # Return to twilio immidiately, then wait 1 minute, and call again
    thread = threading.Thread(target=start_call, args=(json_data, retry, 60 * retry))
    thread.start()
    return f"Waiting {retry} minute(s) to call again"
  else:
     return "Process ended successfully"

@app.route('/make-call', methods=['POST'])
def make_call():
  json_data = request.json
  json_data['next_retry'] = 1
  json_data['last_twilio_response'] = {}

  return f"Call placed successfully ID: {start_call(json_data=json_data, retry=0, delay=0)}"

def start_call(json_data, retry, delay):
  if delay > 0:
     time.sleep(delay)

  client = Client(account_sid, auth_token)

  id = json_data['alert_group_id']

  current_person = getUserMobile(json_data['users_to_be_notified'], retry)
  json_data['current_person'] = current_person
  save_data(id, json.dumps(json_data, indent=4, sort_keys=True))

  say_url = f"{os.environ['DOMAIN']}/get/{id}"

  # Call next user to be notified on the list of users_to_be_notified or default if no users to be notified
  call = client.calls.create(
    method="GET",
    status_callback=f"{os.environ['DOMAIN']}/call-update/{id}",
    status_callback_method="POST",
    url = say_url,
    to = current_person['mobile'],
    from_ = os.environ["FROM_NUMBER"]
  )

  return (call.sid)

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5051, debug=True)
  # from waitress import serve
  # serve(app, host="0.0.0.0", port=5051)
