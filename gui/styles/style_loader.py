import json
import os
import logging

from utils.files import get_resource_path

log = logging.getLogger(__name__)

def apply_stylesheet(app, theme_file='gui/styles/colors.json', qss_file='gui/styles/styles.qss'):
    json_path = get_resource_path(theme_file)
    qss_path = get_resource_path(qss_file)

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            colors = json.load(f)

        with open(qss_path, 'r', encoding='utf-8') as f:
            qss_content = f.read()

        sorted_colors = sorted(colors.items(), key=lambda item: len(item[0]), reverse=True)
        for key, value in sorted_colors:
            qss_content = qss_content.replace(f"@{key}", value)

        app.setStyleSheet(qss_content)
    except FileNotFoundError as e:
        raise Exception(f"Error loading stylesheet: {e}")
    except json.JSONDecodeError as e:
        raise Exception(f"Error parsing JSON theme: {e}")