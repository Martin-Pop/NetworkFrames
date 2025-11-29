import json

def load_json_from_file(file_name: str) -> dict:
    try:
        with open(file_name) as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        raise FileNotFoundError(f"File {file_name} was not found not found.")
    except Exception as e:
        raise e