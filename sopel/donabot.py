"""
Donation Bot module.

Configuration:

  [donabot]
  mode = <sandbox or live>
  client_id = <PayPal client ID>
  client_secret = <PayPal client secret>
  web_endpoint = <Flask site endpoint (host:port)>
"""

from paypalrestsdk import Api, Payment, ResourceNotFound
import sopel.module

from pprint import pprint

def create_api(config):
  return Api({
      "mode": config.mode,
      "client_id": config.client_id,
      "client_secret": config.client_secret,
  })

def setup(bot):
  pass

@sopel.module.interval(60 * 60 * 24)
def remind_people(bot):
  message = (
    "*** Like this chat? Want to support it? Type \".donate 5\" " +
    "(or any other amount you like)!"
  )
  bot.msg(bot.config.donabot.channel, message)

@sopel.module.rule(r"\.donate (\d+)")
def donate(bot, trigger):
  api = create_api(bot.config.donabot)
  currency = "EUR"

  amount = float(trigger.group(1))
  bot.reply("Just a moment, contacting PayPal...")

  return_url = "http://{}/return?nickname={}" \
    .format(bot.config.donabot.web_endpoint, bot.nick)
  cancel_url = "http://{}/cancel".format(bot.config.donabot.web_endpoint)

  payment = Payment({
      "intent": "authorize",
      "payer": {"payment_method": "paypal"},
      "redirect_urls": {
        "return_url": return_url,
        "cancel_url": cancel_url,
      },

      "transactions": [
        {
          "description": "Donation for Stefan Schindler",
          "amount": {
            "total": amount,
            "currency": currency,
          },
        },
      ],
  }, api=api)

  create_result = payment.create()

  if create_result is True:
    links = [link for link in payment.links if link.method == "REDIRECT"]

    if len(links) < 1:
      bot.msg(trigger.nick, "An error occured. :-(")

    else:
      link = links[0]

      bot.msg(
        trigger.nick,
        "Please visit the following URL to authorize the donation: {}" \
          .format(link.href),
      )

  else:
    bot.msg(trigger.nick, "Payment couldn't be created.")

@sopel.module.rule(r"DBP-(.+)")
def finish_payment(bot, trigger):
  api = create_api(bot.config.donabot)
  payment_id = trigger.group(1)
  bot.msg(trigger.nick, "Hold on, checking your payment...")

  try:
    payment = Payment.find(payment_id, api=api)

  except ResourceNotFound:
    payment = None

  if payment is not None:
    payer_id = payment["payer"]["payer_info"]["payer_id"]
    result = payment.execute({"payer_id": payer_id})

    if result is True:
      amount = float(payment["transactions"][0]["amount"]["total"])
      currency = payment["transactions"][0]["amount"]["currency"]

      channel = bot.config.donabot.channel

      bot.write(("MODE", channel, "+v", trigger.nick))
      bot.msg(
        channel,
        "*** {} just donated {:.2f} {}!".format(trigger.nick, amount, currency)
      )
      bot.msg(trigger.nick, "Thank you for your support!")

    else:
      bot.msg(trigger.nick, "Unable to execute the payment. :-(")

  else:
    bot.msg(trigger.nick, "I'm sorry, but I can't find your payment. :-(")
