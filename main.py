import os
import subprocess
#import tkinter


import whisper
from whisper.utils import get_writer

VALID_EXTS = ('.mp3', '.wav', '.ogg', '.mp4', '.m4a', '.flac')
OUTPUT_FOLDER = './transcriptions/'
MODEL_PATH = os.path.join('models', 'large-turbo.pt')

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def get_transcribe(audio_path: str, language: str = 'Russian'):
    return model.transcribe(audio=audio_path, language=language, verbose=True)


def save_file(results, format='txt'):
    writer = get_writer(format, OUTPUT_FOLDER)
    filename = f'transcribe_{input_audio_path}.{format}'
    writer(results, filename)


if os.path.exists(MODEL_PATH):
    print('Загружаем модель из локального файла')
    model = whisper.load_model(MODEL_PATH)
else:
    print('Локальной модели нет, скачиваем...')
    model = whisper.load_model('large')


if __name__ == '__main__':
    input_audio_path = input('Введите путь до файла: ')
    if not input_audio_path.lower().endswith(VALID_EXTS):
        print('Неподдерживаемый формат файла.')
    elif not os.path.exists(input_audio_path):
        print('Файл не найден.')
    else:
        result = get_transcribe(audio_path=input_audio_path)
        print('-' * 50)
        save_file(result, 'txt')
        save_file(result, 'srt')
