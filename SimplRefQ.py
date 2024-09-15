import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import motor.motor_asyncio
import uuid

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

if not BOT_TOKEN or not MONGO_URI:
    raise ValueError("Bot token or MongoDB URI not found in .env file.")

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB setup
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client.simpl_bot
users_collection = db.users

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    referral_code = str(uuid.uuid4())[:8]
    
    existing_user = await users_collection.find_one({"telegram_id": user.id})
    
    if existing_user:
        await update.message.reply_text(f"Welcome back, {user.first_name}! Your referral code is: {existing_user['referral_code']}")
    else:
        new_user = {
            "telegram_id": user.id,
            "referral_code": referral_code,
            "points": 0,
            "referrer_id": None
        }
        await users_collection.insert_one(new_user)
        await update.message.reply_text(f"Welcome, {user.first_name}! Your unique referral code is: {referral_code}")

async def my_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    
    user_data = await users_collection.find_one({"telegram_id": user.id})
    if not user_data:
        await update.message.reply_text("You haven't registered yet. Use /start to register.")
        return

    user_points = user_data['points']
    direct_referrals = await users_collection.count_documents({"referrer_id": user.id})
    
    pipeline = [
        {"$match": {"referrer_id": user.id}},
        {"$lookup": {
            "from": "users",
            "localField": "telegram_id",
            "foreignField": "referrer_id",
            "as": "indirect_referrals"
        }},
        {"$project": {"indirect_count": {"$size": "$indirect_referrals"}}}
    ]
    indirect_referrals = sum([doc['indirect_count'] async for doc in users_collection.aggregate(pipeline)])
    
    await update.message.reply_text(f"Your Simpl Points: {user_points}\n"
                                    f"Direct Referrals: {direct_referrals}\n"
                                    f"Indirect Referrals: {indirect_referrals}")

async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("Please provide a referral code.")
        return
    
    referral_code = context.args[0]
    referrer = await users_collection.find_one({"referral_code": referral_code})
    
    if not referrer:
        await update.message.reply_text("Invalid referral code.")
        return
    
    referrer_id = referrer['telegram_id']
    user_data = await users_collection.find_one({"telegram_id": user.id})
    
    if user_data['referrer_id']:
        await update.message.reply_text("You've already been referred.")
        return
    
    await users_collection.update_one(
        {"telegram_id": user.id},
        {"$set": {"referrer_id": referrer_id}}
    )
    
    referral_count = await users_collection.count_documents({"referrer_id": referrer_id})
    
    if referral_count <= 100:
        await users_collection.update_one(
            {"telegram_id": referrer_id},
            {"$inc": {"points": 10}}
        )
        await update.message.reply_text("Referral successful! The referrer has been awarded 10 Simpl Points.")
    else:
        await update.message.reply_text("Referral successful, but the referrer has reached the maximum referral limit.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Update {update} caused error {context.error}")

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("my_referrals", my_referrals))
    application.add_handler(CommandHandler("refer", refer))

    application.add_error_handler(error_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()