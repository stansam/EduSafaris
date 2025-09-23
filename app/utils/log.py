import logging 
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")

os.makedirs(LOG_DIR, exist_ok=True)

def init_logs():
    log_format = "[%(asctime)s] | [%(levelname)s] | [%(name)s] | line:%(lineno)d | %(message)s"

    logging.basicConfig(
        filename=LOG_FILE,
        filemode="a",  
        format=log_format,
        level=logging.DEBUG,
        encoding="utf-8"
    )

# Creation of logs folder 
# log_dir = "logs"
# os.makedirs(log_dir, exist_ok=True)

# # Formatter
# formatter = logging.Formatter(
#     "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
#     "%Y-%m-%d %H:%M:%S"
# )

# File handler (resets after certain file size, to prevent infinite growth)
# file_handler = RotatingFileHandler(
#     os.path.join(log_dir, "app.log"), maxBytes=10*1024*1024, backupCount=5
# )
# file_handler.setLevel(logging.DEBUG)
# file_handler.setFormatter(formatter)

# # Stream handler (console)
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.DEBUG)
# console_handler.setFormatter(formatter)

# # Attach handlers to app.logger
# app.logger.setLevel(logging.DEBUG)
# app.logger.addHandler(file_handler)
# app.logger.addHandler(console_handler)