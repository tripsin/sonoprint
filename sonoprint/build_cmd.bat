pyinstaller --noconsole --onefile --clean --noconfirm --icon=..\icons\sonoprint.ico sonoprint.py
copy /Y .\settings.ini .\dist\settings.ini