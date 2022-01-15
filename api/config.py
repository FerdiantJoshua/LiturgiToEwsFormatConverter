from environs import Env


env = Env()
env.read_env()

API_CONFIG = {
    'hostname': env.str('HOSTNAME'),
    'port': env.int('PORT'),
}
