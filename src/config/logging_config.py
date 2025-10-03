import logging
import sys
import colorlog

# Remove existing handlers to prevent duplicate logs
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Define color log format
log_colors = {
    'DEBUG': 'cyan',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bold_red',
}

log_formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(levelname)-8s%(reset)s %(asctime)s %(message)s",
    log_colors=log_colors,
    reset=True
)

# Create handler for logging to console
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change to INFO or WARNING in production
    handlers=[console_handler]
)

# Create the logger
logger = logging.getLogger("default")