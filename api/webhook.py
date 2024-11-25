# api/webhook.py
import json
from telegram import Update
from telegram.ext import ApplicationBuilder
from SimplRefQ import start, button  # Import start and button functions from SimplRefQ.py

def handler(request):
    if request.method == 'POST':
        update = json.loads(request.body)  # Get the update sent by Telegram
        print(update)  # For debugging purposes, log the update

        # Create an Update object from the JSON payload
        telegram_update = Update.de_json(update, application.bot)

        # You can add your handlers here manually or trigger them using the application
        application.update_queue.put(telegram_update)  # This queues the update for processing
        return "OK", 200
    else:
        return "Method Not Allowed", 405
