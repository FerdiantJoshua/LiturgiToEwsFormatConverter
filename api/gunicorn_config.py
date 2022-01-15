from environs import Env
from logging_config import LOGGING_CONFIG

env = Env()
env.read_env()

bind = f'{env.str("HOSTNAME")}:{env.int("PORT")}'
timeout = env.int('GUNICORN_TIMEOUT', 300)
workers = env.int('GUNICORN_WORKERS', 2)
worker_class = env.str('GUNICORN_WORKER_CLASS', 'uvicorn.workers.UvicornWorker')
proc_name = env.str('GUNICORN_PROC_NAME', 'liturgi_format_converter')
logconfig_dict = LOGGING_CONFIG
