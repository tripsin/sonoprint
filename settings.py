import os
import sys
from configparser import ConfigParser, Error

CONFIG_FILE_NAME = 'settings.ini'
MAIN_SECTION = 'SETTINGS'
config_path = os.path.join('./', CONFIG_FILE_NAME)


class Settings:
    def __init__(self):
        try:
            self.config = ConfigParser()
            self.config.read(config_path)
            self.option_names = self.config.options(MAIN_SECTION)
        except Error as e:
            print('SETTINGS ERROR:', e.message)
            sys.exit(-1)

    def __getattr__(self, name: str):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            pass

        if name in self.option_names:
            return self.config.get(MAIN_SECTION, name)
        else:
            print('SETTINGS ERROR: No option {} in {}'.format(name, config_path))
            sys.exit(-1)


settings = Settings()
