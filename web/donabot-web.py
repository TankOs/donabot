#!/usr/bin/env python3

from flask import Flask, render_template, request

from pprint import pprint
import json

app = Flask(__name__)
config = None

# Load config.
with open("config.json", "r") as config_stream:
  config = json.load(config_stream)

def create_api(config):
  return Api({
      "mode": config["mode"],
      "client_id": config["client_id"],
      "client_secret": config["client_secret"],
  })

@app.route("/return")
def paypal_return():
  kwargs = {
    "bot_nickname": request.args["nickname"],
    "payment_id": request.args["paymentId"],
  }

  return render_template("return.html", **kwargs)

@app.route("/cancel")
def paypal_cancel():
  return "Too bad :-("

# Run
debug_enabled = config.get("debug", False)
app.run(debug=debug_enabled)
