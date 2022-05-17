import json
import logging

import interactions

import firebase_admin
from firebase_admin import credentials, db


# Set up logging
_logger = logging.getLogger("main")
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    level=logging.INFO,
    force=True,
)

# Load in our secrets and configuration
try:
    import secrets
except ImportError:
    _logger.error(
        "secrets.py not found. Please copy secrets.example.py to secrets.py and fill in your secrets."
    )
    exit(1)


bot = interactions.Client(token=secrets.BOT_TOKEN)


@bot.command(
    name="print",
    description="Prints a message to the Paper Crumpler 🖨",
    scope=secrets.GUILD_ID,
    options=[
        interactions.Option(
            name="text",
            description="Something cool you want printed!",
            type=interactions.OptionType.STRING,
            required=True,
        ),
    ],
)
async def print_message(ctx: interactions.CommandContext, text: str):
    nick = ctx.author.nick or ctx.author.user.username
    logging.info(f"Printing message: [{nick}@discord] {text}")
    send_print_server_message(text, nick)
    await ctx.send(
        f"Printing message: `[{nick}@discord] {text}`",
        # ephemeral=True,
    )


def send_print_server_message(message: str, sender: str):
    db.reference("/pendingMessages").push(
        {
            "message": message,
            "createdAt": {".sv": "timestamp"},
            "source": "discord",
            "sender": sender,
        }
    )


if __name__ == "__main__":

    _logger.info("Started Paper Crumpler Print Server")

    # Connect to Firebase
    try:
        cred = credentials.Certificate("adminsdkcreds.json")
        _logger.info("Firebase Admin SDK credentials loaded")
    except Exception as e:
        _logger.critical("Failed to initialize Firebase Admin SDK: {0}".format(e))
        exit(1)

    _logger.info("Initializing Firebase Realtime Database app")
    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL": secrets.RTDB_URL,
            "databaseAuthVariableOverride": {"uid": "discord-receiver"},
        },
    )
    _logger.info("Firebase Realtime Database app initialized")

    # Start the Discord bot client
    bot.start()
