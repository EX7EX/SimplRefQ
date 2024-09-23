from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import logging

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Load environment variables from .env file
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if TELEGRAM_BOT_TOKEN is None:
    logging.error("No token found. Please check your .env file.")
    exit(1)

# MongoDB connection
try:
    client = MongoClient('mongodb+srv://adesidaadebola1:Pheonix148%24%24@cluster0.xew48.mongodb.net/Cluster0?retryWrites=true&w=majority')
    db = client['Cluster0']
    users_collection = db['users']
except Exception as e:
    logging.error(f"Failed to connect to MongoDB: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat_id = update.effective_chat.id
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Begin Your Journey", callback_data='begin_journey')],
            [InlineKeyboardButton("Invite Friends", callback_data='invite_friends')],
            [InlineKeyboardButton("Leaderboard", callback_data='leaderboard')],
            [InlineKeyboardButton("Balance", callback_data='balance')],
            [InlineKeyboardButton("Wallet", callback_data='wallet')],
            [InlineKeyboardButton("Ranking", callback_data='ranking')]
        ])
        await context.bot.send_message(chat_id=chat_id, text="Welcome to the bot! Choose an option:", reply_markup=reply_markup)
    except AttributeError as e:
        logging.error(f"Error in start handler: {e}")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # Acknowledge the callback query

    if query.data == 'begin_journey':
        await begin_journey(update, context)
    elif query.data == 'invite_friends':
        await invite_friends(update, context)
    elif query.data == 'leaderboard':
        await leaderboard(update, context)
    elif query.data == 'balance':
        await balance(update, context)
    elif query.data == 'wallet':
        await wallet(update, context)
    elif query.data == 'ranking':
        await ranking(update, context)
    else:
        await query.message.reply_text("Unknown action.")

async def begin_journey(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # This function will be implemented to open the mini-app
    await update.callback_query.message.reply_text("The journey begins! (Mini-app integration pending)")

async def invite_friends(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.callback_query.from_user
    username = user.username or user.id
    referral_link = f"https://t.me/SimplQ_bot?start={username}"
    await update.callback_query.message.reply_text(f"Share this link with your friends: {referral_link}")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        top_users = users_collection.find().sort("score", pymongo.DESCENDING).limit(10)
        leaderboard_text = "🏆 Leaderboard 🏆\n\n"
        for i, user in enumerate(top_users, 1):
            leaderboard_text += f"{i}. {user.get('username', 'Anonymous')}: {user.get('score', 0)} points\n"
        await update.callback_query.message.reply_text(leaderboard_text)
    except Exception as e:
        logging.error(f"Error retrieving leaderboard: {e}")
        await update.callback_query.message.reply_text("Error retrieving leaderboard data.")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.callback_query.from_user.id
    try:
        user_data = users_collection.find_one({"user_id": user_id})
        if user_data:
            await update.callback_query.message.reply_text(f"Your current balance: {user_data.get('balance', '0')} $REBLCOINS")
        else:
            await update.callback_query.message.reply_text("No balance data found.")
    except Exception as e:
        logging.error(f"Error retrieving balance: {e}")
        await update.callback_query.message.reply_text("Error retrieving balance data.")

async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.callback_query.from_user.id
    try:
        user_data = users_collection.find_one({"user_id": user_id})
        if user_data:
            await update.callback_query.message.reply_text(f"Your ranking: {user_data.get('rank', 'N/A')}")
        else:
            await update.callback_query.message.reply_text("No ranking data found.")
    except Exception as e:
        logging.error(f"Error retrieving ranking: {e}")
        await update.callback_query.message.reply_text("Error retrieving ranking data.")

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.callback_query.from_user.id
    try:
        user_data = users_collection.find_one({"user_id": user_id})
        if user_data:
            await update.callback_query.message.reply_text(f"Your wallet balance: {user_data.get('balance', '0')} $REBLCOINS")
        else:
            await update.callback_query.message.reply_text("No wallet data found.")
    except Exception as e:
        logging.error(f"Error retrieving wallet data: {e}")
        await update.callback_query.message.reply_text("Error retrieving wallet data.")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))

    # Increase timeout
    application.bot.request.timeout = 30  # Set timeout to 30 seconds

    application.run_polling()