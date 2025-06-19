import os
import tkinter as tk
from tkinter import filedialog, messagebox
import whisper
from whisper.utils import get_writer

# Константы
VALID_EXTS = ('.mp3', '.wav', '.ogg', '.mp4', '.m4a', '.flac')
OUTPUT_FOLDER = './transcriptions/'
MODEL_PATH = os.path.join('models', 'large-turbo.pt')

# Создание выходной папки
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Глобальные переменные
model = None



def load_model():
    global model
    if model is not None:
        return
    if os.path.exists(MODEL_PATH):
        print('Загружаем модель из локального файла')
        model = whisper.load_model(MODEL_PATH)
    else:
        print('Локальной модели нет, скачиваем...')
        model = whisper.load_model('large')


def get_transcribe(audio_path: str, language: str = 'Russian'):
    return model.transcribe(audio=audio_path, language=language, verbose=True)


def save_file(results, input_audio_path, format='txt'):
    writer = get_writer(format, OUTPUT_FOLDER)
    basename = os.path.splitext(os.path.basename(input_audio_path))[0]
    filename = f'{basename}_transcribe.{format}'
    writer(results, filename)


def open_audio_file():
    path = filedialog.askopenfilename(title="Выберите аудиофайл", filetypes=[
        ("Аудиофайл", "*.m4a"),
        ("Аудиофайл", "*.mp3"),
        ("Аудиофайл", "*.wav"),
        ("Аудиофайл", "*.ogg"),
        ("Аудиофайл", "*.mp4"),
        ("Аудиофайл", "*.flac"),
    ])
    if path:
        audio_path_var.set(path)  # Обновляем переменную, связанная с Entry
        
def open_text_file():
    text_file_path = filedialog.askopenfilename(
        title="Выберите файл текста",
        filetypes=[
            ("Текст", "*.txt"),
            ("Текст", "*.srt"),
            ("Текст", "*.tsv"),
        ],
        initialdir=OUTPUT_FOLDER
    )
    if text_file_path:
        with open(text_file_path, 'r', encoding="utf8") as f:
            fileText = f.read()
            text_output.delete(1.0, tk.END)
            text_output.insert(0.0, fileText)

def decode_audio_file():
    path = audio_path_var.get()
    if not path or not os.path.exists(path):
        messagebox.showerror("Ошибка", "Файл не выбран или не существует.")
        return
    if not path.lower().endswith(VALID_EXTS):
        messagebox.showerror("Ошибка", "Формат файла не поддерживается.")
        return

    load_model()
    results = get_transcribe(path)
    text_output.delete("1.0", tk.END)  # Очистка предыдущего текста
    text_output.insert(tk.END, results["text"])  # Вставка нового текста
    save_file(results, path, 'srt')
    messagebox.showinfo("Готово", "Распознавание завершено и srt-файл сохранён.")

def save_text_file():
    text = text_output.get("1.0", tk.END).strip()  # Получаем текст из Text
    if not text:
        messagebox.showwarning("Пусто", "Нет текста для сохранения.")
        return

    save_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")],
        title="Сохранить как..."
    )
    if save_path:
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(text)
            messagebox.showinfo("Готово", f"Файл сохранён:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

# Интерфейс
window = tk.Tk()
audio_path_var = tk.StringVar()  # Переменная для хранения пути к файлу
result_path_var = tk.StringVar() # Переменная для хранения результата
window.title('Whisper Tk GUI')
window.geometry('600x700')

tk.Label(window, text='Программа преобразует аудио в текст с помощью Whisper', font='Arial 12').pack(pady=10)

frame = tk.LabelFrame(window, text='Файл и действия', padx=10, pady=10)
frame.pack(padx=10, pady=10, fill='both', expand=True)

tk.Button(frame, text='Выбрать аудиофайл', command=open_audio_file).pack( pady=5)

tk.Label(frame, text='Выбранный файл').pack()
entry_audio_path = tk.Entry(frame, textvariable=audio_path_var, width=80)
entry_audio_path.pack( pady=5)

tk.Button(frame, text='Начать декодирование', command=decode_audio_file).pack( pady=10)
tk.Label(frame, text='Результат (можно отредактировать перед сохранением)').pack()

text_output = tk.Text(frame, wrap='word', height=20, width=80)
text_output.pack()

tk.Button(frame, text='Сохранить как txt', command=save_text_file).pack( pady=10)

# Меню
menubar = tk.Menu(window)
open_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Открыть...", menu=open_menu)
open_menu.add_command(label="Аудио", command=open_audio_file)
open_menu.add_command(label="Текст", command=open_text_file)
menubar.add_command(label='Выход', command=window.quit)
window.config(menu=menubar)

window.mainloop()
