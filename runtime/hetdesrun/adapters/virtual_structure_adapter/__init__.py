try:
    with open("VERSION", encoding="utf8") as version_file:
        VERSION = version_file.read().strip()
except FileNotFoundError:
    VERSION = "dev snapshot"
