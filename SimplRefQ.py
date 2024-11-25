import requests
import pytz
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, CallbackContext
import pymongo
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv
import os
import logging
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler
import firebase_admin
from firebase_admin import credentials, messaging

# Load environment variables from .env file
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('DB_NAME', 'Cluster0')  # Use environment variable for database name


# Set the webhook URL
WEBHOOK_URL = "https://rebltasks.vercel.app/api/webhook"  # Your Vercel app URL

# Set the webhook with Telegram API
response = requests.post(
    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook",
    json={"url": WEBHOOK_URL},
)

# Optional: Print response to verify if the webhook was set successfully
print(response.json())

def process_data(update: Update, context: CallbackContext):
    # Notify user that data is being processed
    update.message.chat.send_action(action='typing')

    # Simulate a delay (e.g., fetching or processing data)
    time.sleep(2)

    # Send the result once processing is complete
    update.message.reply_text("Data has been processed!")
#Flask setup
app = Flask(__name__)

@app.route('/tasks', methods=['GET'])
def get_tasks():
    """Get all available tasks."""
    tasks = list(tasks_collection.find())  # Fetch tasks from MongoDB
    return jsonify(tasks)

@app.route('/assign_task', methods=['POST'])
def assign_task():
    """Assign a task to a user."""
    user_id = request.json.get("user_id")
    task_id = request.json.get("task_id")
    try:
        assign_task(user_id, task_id)
        return jsonify({"message": "Task assigned successfully."}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 400

@app.route('/claim_reward', methods=['POST'])
def claim_reward():
    """Claim daily reward for a user."""
    user_id = request.json.get("user_id")
    if claim_daily_reward(user_id):
        return jsonify({"message": "Daily reward claimed successfully!"}), 200
    else:
        return jsonify({"message": "You have already claimed your reward today."}), 400

@app.route('/send_notification', methods=['POST'])
def send_notification_api():
    """Trigger a notification to a user."""
    user_id = request.json.get("user_id")
    message = request.json.get("message")
    user = users_collection.find_one({"user_id": user_id})
    if user:
        user_email = user.get("email")
        user_phone = user.get("phone_number")
        send_email(user_email, "Reminder", message)
        send_sms(user_phone, message)
        send_push_notification(user.get("device_token"), "Reminder", message)
        return jsonify({"message": "Notification sent successfully."}), 200
    else:
        return jsonify({"message": "User not found."}), 400

if __name__ == '__main__':
    app.run(debug=True)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


# Ensure Telegram Bot Token is provided
if not TELEGRAM_BOT_TOKEN:
    logging.critical("No Telegram Bot Token found. Please check your .env file.")
    exit(1)

# MongoDB connection handling
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')  # Test connection
    db = client[DB_NAME]
    users_collection = db['users']
    tasks_collection = db['tasks']
    logs_collection = db['audit_logs']
    logging.info(f"Successfully connected to MongoDB database: {DB_NAME}")
except pymongo.errors.PyMongoError as e:
    logging.critical(f"Failed to connect to MongoDB: {e}")
    exit(1)

### User Balance Management ###

def get_user_balance(user_id):
    """Fetch the user's balance from the database."""
    user = users_collection.find_one({"user_id": user_id})
    return user.get("balance", 0) if user else 0

def update_user_balance(user_id, amount):
    """Update the user's balance by the given amount."""
    users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"balance": amount}},
        upsert=True
    )
    log_event(user_id, "balance_update", f"Balance updated by {amount} coins.")

### Task System Integration ###

def create_task(task_name, reward, description=None):
    """Add a new task to the system."""
    tasks_collection.insert_one({
        "task_name": task_name,
        "reward": reward,
        "description": description,
        "created_at": datetime.now()
    })

def assign_task(user_id, task_id):
    """Assign a task to a user."""
    users_collection.update_one(
        {"user_id": user_id},
        {"$push": {"assigned_tasks": task_id}},
        upsert=True
    )

def validate_task_completion(user_id, task_id):
    """Validate task completion and reward the user."""
    task = tasks_collection.find_one({"_id": task_id})
    if not task:
        raise ValueError("Task does not exist.")
    
    user = users_collection.find_one({"user_id": user_id})
    if task_id not in user.get("assigned_tasks", []):
        raise ValueError("Task not assigned to this user.")
    
    # Reward user and mark task as completed.
    update_user_balance(user_id, task["reward"])
    users_collection.update_one(
        {"user_id": user_id},
        {"$pull": {"assigned_tasks": task_id}, "$push": {"completed_tasks": task_id}}
    )
    log_event(user_id, "task_completed", f"Completed task '{task['task_name']}' for {task['reward']} coins.")

### Audit Logs ###

def log_event(user_id, event_type, description):
    """Record significant events in the audit logs."""
    logs_collection.insert_one({
        "user_id": user_id,
        "event_type": event_type,
        "description": description,
        "timestamp": datetime.now()
    })

def get_user_logs(user_id, limit=50):
    """Fetch a user's audit logs."""
    return list(logs_collection.find({"user_id": user_id}).sort("timestamp", DESCENDING).limit(limit))

### Leaderboard and Ranking ###

def get_top_users(limit=10):
    """Fetch the top users based on balance and referrals."""
    return list(users_collection.find().sort([("balance", DESCENDING), ("referrals", DESCENDING)]).limit(limit))

def update_ranking():
    """Update user rankings based on balance and referrals."""
    users = users_collection.find().sort([("balance", DESCENDING), ("referrals", DESCENDING)])
    rank = 1
    for user in users:
        users_collection.update_one(
            {"user_id": user["user_id"]},
            {"$set": {"rank": rank}}
        )
        rank += 1
    log_event(None, "ranking_update", "Leaderboard rankings updated.")

### Notifications ###

def notify_user(user_id, message):
    """Send a notification to a user."""
    # Placeholder function for integration with notification service.
    print(f"Notification to {user_id}: {message}")

def notify_leaderboard_change():
    """Notify users of leaderboard changes."""
    top_users = get_top_users()
    for user in top_users:
        notify_user(user["user_id"], f"Congratulations! You are ranked #{user['rank']} on the leaderboard.")


### Referral Management ###

def add_referral(referrer_id, referred_id):
    """Track referrals and increment referrer's referral count."""
    referrer = users_collection.find_one({"user_id": referrer_id})
    referred = users_collection.find_one({"user_id": referred_id})
    
    # Ensure a user cannot refer themselves or be referred multiple times.
    if referrer_id == referred_id:
        raise ValueError("A user cannot refer themselves.")
    if referred and referred.get("referred_by"):
        raise ValueError("User has already been referred by someone else.")
    
    # Update the referrer's referral count and add the referred user.
    users_collection.update_one(
        {"user_id": referrer_id},
        {"$inc": {"referrals": 1}},
        upsert=True
    )
    users_collection.update_one(
        {"user_id": referred_id},
        {"$set": {"referred_by": referrer_id}},
        upsert=True
    )

def get_referral_count(user_id):
    """Get the total number of referrals for a user."""
    user = users_collection.find_one({"user_id": user_id})
    return user.get("referrals", 0) if user else 0

### Leaderboard and Ranking ###

def get_top_users(limit=10):
    """Fetch the top users based on balance and referrals."""
    return list(users_collection.find().sort([("balance", -1), ("referrals", -1)]).limit(limit))

def update_ranking():
    """Update user rankings based on balance and referrals."""
    users = users_collection.find().sort([("balance", -1), ("referrals", -1)])
    rank = 1
    for user in users:
        users_collection.update_one(
            {"user_id": user["user_id"]},
            {"$set": {"rank": rank}}
        )
        rank += 1

### Daily Rewards ###

def check_daily_reward(user_id):
    """Check if the user has claimed their daily reward."""
    user = users_collection.find_one({"user_id": user_id})
    last_claimed = user.get("last_daily_reward") if user else None
    if not last_claimed:
        return True
    last_claimed_date = datetime.strptime(last_claimed, "%Y-%m-%d")
    return (datetime.now() - last_claimed_date).days >= 1

def claim_daily_reward(user_id, reward_amount=10):
    """Allow the user to claim their daily reward if eligible."""
    if check_daily_reward(user_id):
        update_user_balance(user_id, reward_amount)
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_daily_reward": datetime.now().strftime("%Y-%m-%d")}},
            upsert=True
        )
        log_event(user_id, "daily_reward", f"Claimed daily reward of {reward_amount} coins.")
        notify_user(user_id, f"You've claimed your daily reward of {reward_amount} coins!")
        return True
    return False

### Performance Optimization ###

def create_indexes():
    """Ensure necessary indexes exist for optimal performance."""
    users_collection.create_index([("balance", DESCENDING)])
    users_collection.create_index([("referrals", DESCENDING)])
    users_collection.create_index([("rank", ASCENDING)])
    logs_collection.create_index([("timestamp", DESCENDING)])
    print("Indexes created.")

### Wallet Management ###

def transfer_balance(sender_id, receiver_id, amount):
    """Transfer balance from one user to another."""
    sender_balance = get_user_balance(sender_id)
    if sender_balance < amount:
        raise ValueError("Insufficient balance.")
    
    # Deduct from sender and add to receiver.
    update_user_balance(sender_id, -amount)
    update_user_balance(receiver_id, amount)

## Utility Functions ###

def create_user(user_id, username=None):
    """Create a new user entry in the database."""
    existing_user = users_collection.find_one({"user_id": user_id})
    if existing_user:
        raise ValueError("User already exists.")
    users_collection.insert_one({
        "user_id": user_id,
        "username": username,
        "balance": 0,
        "referrals": 0,
        "rank": None,
        "last_daily_reward": None,
        "referred_by": None,
        "assigned_tasks": [],
        "completed_tasks": []
    })
    log_event(user_id, "user_created", "New user created.")

def delete_user(user_id):
    """Remove a user from the database."""
    users_collection.delete_one({"user_id": user_id})
    log_event(user_id, "user_deleted", "User removed from the system.")

def get_user_details(user_id):
    """Fetch all details of a user."""
    user = users_collection.find_one({"user_id": user_id})
    return user if user else None

# Define UTC timezone
utc = pytz.UTC

# Helper function: Check if user has joined the required channel
async def has_joined_channel(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id="@simplco", user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.warning(f"Error checking channel membership for user {user_id}: {e}")
        return False

# Updated start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username or f"User_{user_id}"

    # Ensure the user joins the required channel
    if not await has_joined_channel(context, user_id):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please join @simplco to access all bot features!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Channel", url="https://t.me/simplco")]
            ])
        )
        return

    # Initialize user record if not exists
    user_record = users_collection.find_one({"user_id": user_id})
    if not user_record:
        users_collection.insert_one({
            "user_id": user_id,
            "username": username,
            "balance": 0,
            "wallet": 0,
            "rank": None,
            "joined_channel": True,
            "last_claimed": None,
            "tasks_completed": []
        })
        logging.info(f"New user registered: {username} (ID: {user_id})")
    else:
        users_collection.update_one({"user_id": user_id}, {"$set": {"joined_channel": True}})

    # Send main menu
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

# Inline Button Handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    handler_mapping = {
        'invite_friends': invite_friends,
        'leaderboard': leaderboard,
        'balance': balance,
        'wallet': wallet,
        'ranking': ranking,
        'daily_rewards': daily_rewards
    }

    handler = handler_mapping.get(query.data)
    if handler:
        await handler(update, context)
    else:
        fallback_message = "Unknown action. Please choose a valid option from the menu."
        logging.error(f"Unknown callback query: {query.data}")
        await query.message.reply_text(fallback_message)

# Balance Handler
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.callback_query.from_user.id

    # Fetch user data from MongoDB
    user = users_collection.find_one({"user_id": user_id})
    if user:
        balance = user.get("balance", 0)
        await update.callback_query.message.reply_text(f"Your current balance is {balance} $REBLCOINS.")
    else:
        await update.callback_query.message.reply_text("No user record found. Please register using /start.")

# Invite Friends Handler
async def invite_friends(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.callback_query.from_user
    referral_id = user.username if user.username else str(user.id)
    referral_link = f"https://t.me/SimplQ_bot?start={referral_id}"
    await update.callback_query.message.reply_text(f"Share this link with your friends: {referral_link}")

# Leaderboard Handler
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        top_users = users_collection.find().sort("balance", pymongo.DESCENDING).limit(10)
        leaderboard_text = "🏆 Leaderboard 🏆\n\n"
        for i, user in enumerate(top_users, 1):
            username = user.get('username', 'Anonymous')
            leaderboard_text += f"{i}. {username}: {user.get('balance', 0)} $REBLCOINS\n"
        await update.callback_query.message.reply_text(leaderboard_text)
    except Exception as e:
        logging.error(f"Error retrieving leaderboard: {e}")
        await update.callback_query.message.reply_text("Error retrieving leaderboard data.")

# Daily Rewards Handler
async def daily_rewards(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.callback_query.from_user.id
    today = utc.localize(datetime.combine(date.today(), datetime.min.time()))

    user = users_collection.find_one({"user_id": user_id})
    if not user:
        await update.callback_query.message.reply_text("No user record found. Please register using /start.")
        return

    last_claimed = user.get("last_claimed")
    if last_claimed:
        last_claimed = utc.localize(last_claimed) if not last_claimed.tzinfo else last_claimed
        if last_claimed.date() == today.date():
            await update.callback_query.message.reply_text("You've already claimed your daily reward today.")
            return

    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"balance": user.get("balance", 0) + 10, "last_claimed": today}}
    )
    await update.callback_query.message.reply_text("You have successfully claimed 10 $REBLCOINS!")

# Ranking Handler (Optimized for scalability)
async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.callback_query.from_user.id
    user_rank = list(users_collection.aggregate([
        {"$setWindowFields": {
            "partitionBy": None,
            "sortBy": {"balance": -1},
            "output": {
                "rank": {"$rank": {}}
            }
        }},
        {"$match": {"user_id": user_id}}
    ]))

    if user_rank:
        user = user_rank[0]
        rank = user.get("rank")
        balance = user.get("balance", 0)
        await update.callback_query.message.reply_text(f"Your rank: {rank}\nYour balance: {balance} $REBLCOINS.")
    else:
        await update.callback_query.message.reply_text("No user record found. Please register using /start.")

# Wallet Handler
async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.callback_query.from_user.id

    # Fetch user data
    user = users_collection.find_one({"user_id": user_id})
    if user:
        wallet = user.get("wallet", 0)
        balance = user.get("balance", 0)
        await update.callback_query.message.reply_text(f"Your wallet: {wallet}\nYour balance: {balance} $REBLCOINS.")
    else:
        await update.callback_query.message.reply_text("No user record found. Please register using /start.")

# Add Flask API endpoints to sync bot and mini-app data
@app.route('/api/get_user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Fetch user details for mini-app."""
    user = users_collection.find_one({"user_id": user_id})
    if user:
        return {
            "user_id": user.get("user_id"),
            "username": user.get("username", "Anonymous"),
            "balance": user.get("balance", 0),
            "wallet": user.get("wallet", 0),
            "rank": user.get("rank", None),
            "tasks_completed": user.get("tasks_completed", []),
            "last_claimed": user.get("last_claimed")
        }, 200
    else:
        return {"error": "User not found"}, 404

@app.route('/api/update_user/<int:user_id>', methods=['POST'])
def update_user(user_id):
    """Update user data from the mini-app."""
    try:
        data = request.json
        update_data = {}

        if "balance" in data:
            update_data["balance"] = data["balance"]
        if "wallet" in data:
            update_data["wallet"] = data["wallet"]
        if "tasks_completed" in data:
            update_data["tasks_completed"] = data["tasks_completed"]
        if "last_claimed" in data:
            update_data["last_claimed"] = data["last_claimed"]

        if update_data:
            users_collection.update_one({"user_id": user_id}, {"$set": update_data})
            return {"message": "User data updated successfully"}, 200
        else:
            return {"error": "No valid fields to update"}, 400
    except Exception as e:
        logging.error(f"Error updating user {user_id}: {e}")
        return {"error": str(e)}, 500

def daily_reminder():
    """Send daily reminders to all users to claim rewards and complete tasks."""
    users = users_collection.find()
    for user in users:
        user_id = user["user_id"]
        user_email = user.get("email")
        user_phone = user.get("phone_number")
        message = "Don't forget to log in, claim your daily reward, and perform tasks!"
        send_email(user_email, "Daily Reminder", message)
        send_sms(user_phone, message)
        send_push_notification(user.get("device_token"), "Reminder", message)

scheduler = BackgroundScheduler()
scheduler.add_job(daily_reminder, 'interval', days=1)  # Run daily
scheduler.start()

#notifications
def send_push_notification(token, title, body):
    """Send a push notification."""
    # Initialize Firebase Admin SDK
    cred = credentials.Certificate('/Users/mac/Documents/WORKSPACE/untitled folder/journal/private keys/firebase/rebltasks-d156e-c10cc3a3732e.json')
    firebase_admin.initialize_app(cred)

    # Create the message
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        token=token  # User's device token
    )

    # Send the message
    response = messaging.send(message)
    print(f"Push notification sent: {response}")

    send_push_notification(user_device_token, "Daily Reminder", "Don't forget to log in and claim your reward!")


# Telegram Bot Setup
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome to ReblTasks!")

# Telegram Bot application setup
application = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
application.add_handler(CommandHandler("start", start))

@app.route("/webhook", methods=["POST"])
def webhook():
    # Get the JSON update sent by Telegram
    json_update = request.get_json()

    # Convert the update to an Update object and add it to the bot's queue
    update = Update.de_json(json_update, application.bot)
    application.update_queue.put(update)
    return "OK", 200

if __name__ == "__main__":
    # Setup webhook URL dynamically using environment variable
    webhook_url = f"{os.getenv('WEBHOOK_URL')}/webhook"
    
    # Run the bot with webhook on Vercel
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        url_path="webhook",
        webhook_url=webhook_url
    )