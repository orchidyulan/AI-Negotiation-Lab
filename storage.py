import json
import os

DATA_FILE = "data/logs.json"

def save_record(record):
    if not os.path.exists("data"):
        os.makedirs("data")

    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except:
        data = []

    data.append(record)

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_records():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []