import firebase_admin
from firebase_admin import credentials, db

from escpos.printer import Usb

import logging
import traceback

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


class Message:
    def __init__(self, message_data):
        self.id = message_data[0]
        self.text = message_data[1]["message"]
        self.created_at = message_data[1]["createdAt"]
        self.sender = message_data[1]["sender"]
        self.source = message_data[1]["source"]


def process_and_print(message: Message):
    _logger.info(
        f"Printing message: [{message.sender}@{message.source}] {message.text}"
    )
    p.textln(f"[{message.sender}@{message.source}] {message.text}\n\n")

    _logger.info("Storing message in printedMessages")
    db.reference("printedMessages").child(message.id).set(
        {
            "message": message.text,
            "createdAt": message.created_at,
            "sender": message.sender,
            "source": message.source,
            "printedAt": {".sv": "timestamp"},
        }
    )

    _logger.info("Deleting message from pendingMessages")
    db.reference("pendingMessages").child(message.id).delete()


def handle_event(event: db.Event):

    if event.data is None:
        _logger.debug("Ignoring None event")
        return

    _logger.info(f"Handling event: [{event.event_type}] {event.path} {event.data}")

    if event.path == "/":
        # Handle root event with all pending messages
        for message_data in event.data.items():
            try:
                process_and_print(Message(message_data))
            except Exception as e:
                _logger.error(
                    f"Failed to process message, skipping:\n"
                    f"--- Message ---\n"
                    f"{message_data}\n"
                    f"--- Exception ---\n"
                    f"{traceback.format_exc()}"
                )
    else:
        # Handle child event with single message
        try:
            process_and_print(Message((event.path.strip("/"), event.data)))
        except Exception as e:
            _logger.error(
                f"Failed to process message, skipping: \n{traceback.format_exc()}"
            )


if __name__ == "__main__":

    _logger.info("Started Paper Crumpler Print Server")

    # Connect to the thermal printer
    _logger.info("Connecting to USB printer")
    p = Usb(0x0483, 0x070B)
    _logger.info("Connected to USB printer")

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
            "databaseAuthVariableOverride": {"uid": "print-server"},
        },
    )
    _logger.info("Firebase Realtime Database app initialized")

    # Listen for new messages to print (and print any already pending)
    _logger.info("Listening for new messages")
    db.reference("/pendingMessages").listen(handle_event)
