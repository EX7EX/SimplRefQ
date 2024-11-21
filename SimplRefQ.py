from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Load environment variables from .env file
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
MONGO_URI = os.getenv('MONGO_URI')

# Ensure Telegram Bot Token is provided
if TELEGRAM_BOT_TOKEN is None:
    logging.error("No token found. Please check your .env file.")
    exit(1)

# MongoDB connection setup
try:
    client = MongoClient(MONGO_URI)
    db = client['Cluster0']
    users_collection = db['users']
    rankings_collection = db['rankings']
    logging.info("Connected to MongoDB successfully.")
except Exception as e:
    logging.error(f"Failed to connect to MongoDB: {e}")
    exit(1)

# Helper function: Check if user has joined the required channel
async def has_joined_channel(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id="@simplco", user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.warning(f"Error checking channel membership for user {user_id}: {e}")
        return False

# Start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username or "Anonymous"

    # Check if user has joined the required channel
    if not await has_joined_channel(context, user_id):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You must join @simplco to unlock full bot features.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Channel", url="https://t.me/simplco")]
            ])
        )
        return

    # Add user to database if not already present
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({
            "user_id": user_id,
            "username": username,
            "balance": 0,
            "wallet": 0,
            "rank": None,
            "joined_channel": True,
            "last_claimed": None,  # New field to track daily rewards
            "tasks_completed": []  # Initialize as empty list
        })

    # Show main menu with inline buttons
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Launch Mini App", url="t.me/SimplQ_bot/rebltasks")],
        [InlineKeyboardButton("Invite Friends", callback_data='invite_friends')],
        [InlineKeyboardButton("Leaderboard", callback_data='leaderboard')],
        [InlineKeyboardButton("Balance", callback_data='balance')],
        [InlineKeyboardButton("Daily Rewards", callback_data='daily_rewards')],
        [InlineKeyboardButton("Wallet", callback_data='wallet')],
        [InlineKeyboardButton("Ranking", callback_data='ranking')]
    ])

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome to the bot! Choose an option:",
        reply_markup=reply_markup
    )

# Button Handler for Inline Buttons
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # Acknowledge the callback query

    # Handling various callback queries
    if query.data == 'invite_friends':
        await invite_friends(update, context)
    elif query.data == 'leaderboard':
        await leaderboard(update, context)
    elif query.data == 'balance':
        await balance(update, context)
    elif query.data == 'wallet':
        await wallet(update, context)
    elif query.data == 'ranking':
        await ranking(update, context)
    elif query.data == 'daily_rewards':
        await daily_rewards(update, context)
    else:
        await query.message.reply_text("Unknown action.")

# Invite Friends Handler
async def invite_friends(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.callback_query.from_user
    username = user.username or user.id
    referral_link = f"https://t.me/SimplQ_bot?start={username}"
    await update.callback_query.message.reply_text(f"Share this link with your friends: {referral_link}")

# Leaderboard Handler
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        top_users = users_collection.find().sort("balance", pymongo.DESCENDING).limit(10)
        leaderboard_text = "🏆 Leaderboard 🏆\n\n"
        for i, user in enumerate(top_users, 1):
            username = user.get('username', 'Anonymous')
            tasks_count = len(user.get('tasks_completed', []))
            leaderboard_text += f"{i}. {username}: {user.get('balance', 0)} $REBLCOINS\n"
        await update.callback_query.message.reply_text(leaderboard_text)
    except Exception as e:
        logging.error(f"Error retrieving leaderboard: {e}")
        await update.callback_query.message.reply_text("Error retrieving leaderboard data.")

# Balance Handler
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.callback_query.from_user.id
    try:
        user_data = users_collection.find_one({"user_id": user_id})
        if user_data:
            await update.callback_query.message.reply_text(f"Your current balance: {user_data.get('balance', 0)} $REBLCOINS")
        else:
            await update.callback_query.message.reply_text("No balance data found.")
    except Exception as e:
        logging.error(f"Error retrieving balance: {e}")
        await update.callback_query.message.reply_text("Error retrieving balance data.")

# Wallet Handler
async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.callback_query.from_user.id
    try:
        user_data = users_collection.find_one({"user_id": user_id})
        if user_data:
            await update.callback_query.message.reply_text(f"Your wallet balance: {user_data.get('wallet', 0)} $REBLCOINS")
        else:
            await update.callback_query.message.reply_text("No wallet data found.")
    except Exception as e:
        logging.error(f"Error retrieving wallet data: {e}")
        await update.callback_query.message.reply_text("Error retrieving wallet data.")

# Ranking Handler
async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.callback_query.from_user.id
    try:
        user_data = rankings_collection.find_one({"user_id": user_id})
        if user_data:
            await update.callback_query.message.reply_text(f"Your ranking: {user_data.get('rank', 'N/A')}")
        else:
            await update.callback_query.message.reply_text("No ranking data found.")
    except Exception as e:
        logging.error(f"Error retrieving ranking: {e}")
        await update.callback_query.message.reply_text("Error retrieving ranking data.")

# Daily Rewards Handler
async def daily_rewards(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.callback_query.from_user.id
    try:
        user_data = users_collection.find_one({"user_id": user_id})
        if not user_data:
            await update.callback_query.message.reply_text("User not found in the database.")
            return

        # Check if the user already claimed the reward today
        last_claimed = user_data.get("last_claimed")
        if last_claimed:
            last_claimed_date = datetime.strptime(last_claimed, "%Y-%m-%d")
            if last_claimed_date.date() == datetime.utcnow().date():
                await update.callback_query.message.reply_text("You have already claimed your daily reward today. Come back tomorrow!")
                return

        # Add the reward to the user's balance
        daily_reward = 10000
        new_balance = user_data.get("balance", 0) + daily_reward
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"balance": new_balance, "last_claimed": datetime.utcnow().strftime("%Y-%m-%d")}}
        )

        await update.callback_query.message.reply_text(f"🎉 You have claimed your daily reward of {daily_reward} $REBLCOINS! Your new balance is {new_balance} $REBLCOINS.")
    except Exception as e:
        logging.error(f"Error processing daily rewards: {e}")
        await update.callback_query.message.reply_text("An error occurred while claiming your daily reward. Please try again later.")

# Task Completion Handler
async def complete_task(user_id: int, task_id: str) -> None:
    try:
        # Add task completion details
        task_entry = {
            "task_id": task_id,
            "completed": True,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        }

        # Update MongoDB with new task
        users_collection.update_one(
            {"user_id": user_id},
            {"$push": {"tasks_completed": task_entry}}
        )
        logging.info(f"Task '{task_id}' marked as completed for user {user_id}.")
    except Exception as e:
        logging.error(f"Error marking task '{task_id}' as completed for user {user_id}: {e}")

# Main function to set up the bot
async def main():
    # Initialize the bot with the token
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    # Run the bot
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
