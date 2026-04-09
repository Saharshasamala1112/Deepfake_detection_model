import os


def route_input(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext in ['.jpg', '.jpeg', '.png']:
        return 'image'
    elif ext in ['.mp4', '.avi']:
        return 'video'
    elif ext in ['.wav', '.mp3']:
        return 'audio'
    elif ext == '.txt':
        return 'document'
    else:
        return 'unknown'
