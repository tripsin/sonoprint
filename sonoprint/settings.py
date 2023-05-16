import os
import sys
from configparser import ConfigParser, Error
from tools import log_to_file

CONFIG_FILE_NAME = 'settings.ini'
MAIN_SECTION = 'SETTINGS'
config_path = os.path.join('./', CONFIG_FILE_NAME)


def unpack_int(s: str):
    return tuple(map(int, s.split(',')))


class Settings:
    def __init__(self):
        try:
            self.config = ConfigParser()
            self.config.read(config_path)
            self.option_names = self.config.options(MAIN_SECTION)
        except Error as e:
            log_to_file('SETTINGS ERROR: {}'.format(e.message))
            sys.exit(-1)

    def __getattr__(self, name: str):
        name = name.lower()
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            pass

        if name in self.option_names:
            return self.config.get(MAIN_SECTION, name)
        else:
            log_to_file('SETTINGS ERROR: No option {} in {}'.format(name, config_path))
            sys.exit(-1)

    def save(self, option: str, value: str):
        self.config.set('SETTINGS', option, value)
        with open(config_path, "w") as config_file:
            self.config.write(config_file)


if not os.path.isfile(config_path):
    log_to_file('SETTINGS ERROR: {} not found'.format(CONFIG_FILE_NAME))
    sys.exit(-1)

settings = Settings()
