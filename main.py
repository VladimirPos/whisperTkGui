import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk  # Импорт необходимых модулей Tkinter
from tkinterdnd2 import TkinterDnD, DND_FILES  # Для поддержки drag-and-drop
import whisper  # Основная библиотека для распознавания речи
from whisper.utils import get_writer  # Для сохранения результатов
import shutil  # Для работы с файлами
import sys  # Для системных функций

# Константы программы
VALID_EXTS = ('.mp3', '.wav', '.ogg', '.mp4', '.m4a', '.flac')  # Поддерживаемые форматы аудио
OUTPUT_FOLDER = './transcriptions/'  # Папка для сохранения результатов
MODEL_FOLDER = './models/'  # Папка для хранения модели
MODEL_NAME = 'large-v3'  # Название модели Whisper
MODEL_PATH = os.path.join(MODEL_FOLDER, f'{MODEL_NAME}.pt')  # Полный путь к модели

# Создаем необходимые папки, если они не существуют
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(MODEL_FOLDER, exist_ok=True)

# Глобальные переменные
model = None  # Здесь будет храниться загруженная модель
pending_file_path = None  # Путь к выбранному аудиофайлу

# Загружаем модель Whisper, сначала пробуя локальную версию, затем скачивая при необходимости
def load_model():
    global model
    if model is not None:  # Если модель уже загружена
        return model
    
    # Проверяем наличие локальной модели
    if os.path.exists(MODEL_PATH):
        print('Загружаем модель из локального файла')
        try:
            model = whisper.load_model(MODEL_PATH)
            return model
        except Exception as e:
            print(f"Ошибка загрузки локальной модели: {e}")
            # Пробуем удалить поврежденную модель
            try:
                os.remove(MODEL_PATH)
            except:
                pass
    
    # Если локальной модели нет, скачиваем
    print('Локальной модели нет, скачиваем...')
    try:
        model = whisper.load_model(MODEL_NAME)
        
        # Пытаемся сохранить модель локально для будущего использования
        print('Сохраняем модель локально...')
        try:
            # Проверяем стандартные пути к кешу Whisper
            cache_dir = os.path.dirname(whisper.__file__)
            cache_path = os.path.join(cache_dir, 'assets', MODEL_NAME + '.pt')
            
            if not os.path.exists(cache_path):
                cache_path = os.path.join(os.path.expanduser('~'), '.cache', 'whisper', MODEL_NAME + '.pt')
            
            if os.path.exists(cache_path):
                shutil.copy2(cache_path, MODEL_PATH)
                print(f'Модель сохранена в: {MODEL_PATH}')
            else:
                # Альтернативный способ сохранения через torch
                try:
                    import torch
                    torch.save(model.state_dict(), MODEL_PATH)
                    print(f'Модель сохранена напрямую в: {MODEL_PATH}')
                except Exception as torch_error:
                    print(f'Ошибка при сохранении модели через torch: {torch_error}')
                
        except Exception as copy_error:
            print(f'Ошибка при сохранении модели: {copy_error}')
            
        return model
        
    except Exception as e:
        # Формируем подробное сообщение об ошибке
        error_msg = f"Не удалось загрузить модель:\n{str(e)}\n\n"
        error_msg += "Возможные решения:\n"
        error_msg += "1. Проверьте подключение к интернету\n"
        error_msg += "2. Убедитесь, что у вас достаточно места на диске (требуется ~3GB)\n"
        error_msg += "3. Попробуйте установить модель вручную:\n"
        error_msg += f"   - Скачайте large-v3.pt с https://openaipublic.azureedge.net/main/whisper/models/\n"
        error_msg += f"   - Поместите файл в папку {MODEL_FOLDER}\n"
        error_msg += f"4. Проверьте права доступа к папке {MODEL_FOLDER}\n"
        error_msg += "5. Попробуйте запустить программу от имени администратора"
        
        messagebox.showerror("Критическая ошибка", error_msg)
        sys.exit(1)

# Транскрибирование аудио. Язык - русский. TBD - возможность выбора языков
def get_transcribe(audio_path: str, language: str = 'Russian'):
    return model.transcribe(audio=audio_path, language=language, verbose=True)

# Сохранение текстового файла
def save_file(results, input_audio_path, format='txt'):
    writer = get_writer(format, OUTPUT_FOLDER)
    basename = os.path.splitext(os.path.basename(input_audio_path))[0]
    filename = f'{basename}_transcribe.{format}'
    writer(results, filename)

# Выбор аудиофайла
def open_audio_file():
    path = filedialog.askopenfilename(
        title="Выберите аудиофайл", 
        filetypes=[
            ("Аудиофайлы", "*.m4a;*.mp3;*.wav;*.ogg;*.mp4;*.flac"),
            ("Все файлы", "*.*")
        ]
    )
    if path:
        set_pending_file(path)

# Выбор текстового файла для просмотря и/или редактирования
def open_text_file():
    text_file_path = filedialog.askopenfilename(
        title="Выберите файл текста",
        filetypes=[
            ("Текстовые файлы", "*.txt;*.srt;*.tsv"),
            ("Все файлы", "*.*")
        ],
        initialdir=OUTPUT_FOLDER
    )
    if text_file_path:
        try:
            with open(text_file_path, 'r', encoding="utf8") as f:
                fileText = f.read()
                text_output.delete(1.0, tk.END)
                text_output.insert(0.0, fileText)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")

# Путь до выбранного файла
def set_pending_file(path):
    global pending_file_path
    
    # Проверяем расширение файла
    if not path.lower().endswith(VALID_EXTS):
        messagebox.showerror(
            "Ошибка", 
            f"Формат файла не поддерживается. Поддерживаемые форматы: {', '.join(VALID_EXTS)}"
        )
        return
    
    pending_file_path = path
    audio_path_var.set(os.path.basename(path))  # Показываем только имя файла
    entry_audio_path.config(bg='lightyellow')  # Подсвечиваем поле с файлом

# Транскрибирование аудио
def decode_audio_file():
    if not pending_file_path or not os.path.exists(pending_file_path):
        messagebox.showerror("Ошибка", "Файл не выбран или не существует.")
        return
    
    entry_audio_path.config(bg='white')  # Возвращаем стандартный цвет поля
    
    try:
        model = load_model()  # Загружаем модель
    except:
        return
    
    # Создаем окно с индикатором прогресса
    progress_window = tk.Toplevel(window)
    progress_window.title("Обработка")
    progress_window.geometry("400x150")
    progress_window.resizable(False, False)
    
    # Центрируем окно прогресса
    window_width = window.winfo_width()
    window_height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width/2) - (window_width/2)
    y = (screen_height/2) - (window_height/2)
    progress_window.geometry(f"+{int(x)}+{int(y)}")
    
    # Элементы окна прогресса
    tk.Label(progress_window, text="Идёт распознавание...", font=('Arial', 12)).pack(pady=10)
    progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
    progress_bar.pack(pady=10, padx=20, fill='x')
    progress_bar.start()
    
    tk.Label(
        progress_window, 
        text="Пожалуйста, подождите. Это может занять несколько минут.", 
        font=('Arial', 9)
    ).pack(pady=5)
    
    progress_window.update()
    
    try:
        # Выполняем распознавание
        results = get_transcribe(pending_file_path)
        
        # Выводим результат
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, results["text"])
        
        # Сохраняем результат
        save_file(results, pending_file_path, 'srt')
        messagebox.showinfo(
            "Готово", 
            "Распознавание завершено!\nТекст сохранён в папке 'transcriptions'."
        )
    except Exception as e:
        messagebox.showerror(
            "Ошибка", 
            f"Произошла ошибка при обработке файла:\n{str(e)}"
        )
    finally:
        progress_window.destroy()  # Закрываем окно прогресса

# Cохранение текста из поля вывода в файл
def save_text_file():
    text = text_output.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("Пусто", "Нет текста для сохранения.")
        return

    save_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[
            ("Текстовые файлы", "*.txt"),
            ("Субтитры", "*.srt"),
            ("Все файлы", "*.*")
        ],
        title="Сохранить текст как...",
        initialdir=OUTPUT_FOLDER
    )
    if save_path:
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(text)
            messagebox.showinfo(
                "Готово", 
                f"Файл успешно сохранён:\n{save_path}"
            )
        except Exception as e:
            messagebox.showerror(
                "Ошибка", 
                f"Не удалось сохранить файл:\n{e}"
            )

# Обработка drag-n-drop
def handle_drop(event):
    files = window.tk.splitlist(event.data)
    if files:
        set_pending_file(files[0])

# Обработка закрытия окна
def on_closing():
    if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
        window.destroy()

# ===== ГРАФИЧЕСКИЙ ИНТЕРФЕЙС =====

window = TkinterDnD.Tk()  # Главное окно с поддержкой drag-and-drop
audio_path_var = tk.StringVar()  # Переменная для хранения пути к файлу

# Настройки главного окна
window.title('Whisper Audio to Text Converter')
window.geometry('750x800')
window.minsize(700, 700)

# Настройка drag-and-drop
window.drop_target_register(DND_FILES)
window.dnd_bind('<<Drop>>', handle_drop)

# Главный контейнер
main_frame = tk.Frame(window, bg='#f0f0f0')
main_frame.pack(fill='both', expand=True, padx=10, pady=10)

# Заголовок
header_frame = tk.Frame(main_frame, bg='#f0f0f0')
header_frame.pack(fill='x', pady=(0, 10))

tk.Label(
    header_frame, 
    text='Whisper Audio to Text Converter', 
    font=('Arial', 14, 'bold'),
    bg='#f0f0f0'
).pack()

tk.Label(
    header_frame, 
    text='Преобразует аудио в текст с помощью модели Whisper large-v3', 
    font=('Arial', 10),
    bg='#f0f0f0'
).pack(pady=(5, 0))

# Фрейм для работы с файлами
file_frame = tk.LabelFrame(
    main_frame, 
    text=' Файл ', 
    bg='#f0f0f0', 
    padx=10, 
    pady=10
)
file_frame.pack(fill='x', pady=5)

# Кнопки выбора файла
button_frame = tk.Frame(file_frame, bg='#f0f0f0')
button_frame.pack(fill='x', pady=5)

tk.Button(
    button_frame, 
    text='Выбрать аудиофайл', 
    command=open_audio_file
).pack(side='left', padx=5)

tk.Button(
    button_frame, 
    text='Открыть текст', 
    command=open_text_file
).pack(side='left', padx=5)

# Поле с путем к файлу
tk.Label(
    file_frame, 
    text='Выбранный файл:', 
    bg='#f0f0f0'
).pack(anchor='w')

entry_audio_path = tk.Entry(
    file_frame, 
    textvariable=audio_path_var, 
    width=60, 
    bg='white'
)
entry_audio_path.pack(fill='x', pady=5)

# Подсказка для drag-and-drop
drag_drop_label = tk.Label(
    file_frame, 
    text='Перетащите аудиофайл сюда',
    fg='gray',
    bg='#f0f0f0',
    font=('Arial', 8)
)
drag_drop_label.pack(fill='x')

# Кнопка обработки
process_button = tk.Button(
    file_frame, 
    text='Начать распознавание', 
    command=decode_audio_file,
    bg='#4CAF50',
    fg='white'
)
process_button.pack(pady=10)

# Фрейм для результатов
result_frame = tk.LabelFrame(
    main_frame, 
    text='Результат распознавания. Полученный текст можно отредактировать перед сохранением.', 
    bg='#f0f0f0', 
    padx=10, 
    pady=10
)
result_frame.pack(fill='both', expand=True, pady=5)

# Текстовое поле с прокруткой
text_scroll = tk.Scrollbar(result_frame)
text_scroll.pack(side='right', fill='y')

text_output = tk.Text(
    result_frame, 
    wrap='word', 
    height=20, 
    width=80,
    font=('Arial', 10),
    yscrollcommand=text_scroll.set,
    bg='white'
)
text_output.pack(fill='both', expand=True)

text_scroll.config(command=text_output.yview)

# Кнопка сохранения
save_button = tk.Button(
    result_frame, 
    text='Сохранить текст', 
    command=save_text_file,
    bg='#2196F3',
    fg='white'
)
save_button.pack(pady=10)

# Статус бар
status_bar = tk.Label(
    window, 
    text='Готов к работе', 
    relief='sunken', 
    anchor='w',
    font=('Arial', 8),
    bg='#e0e0e0'
)
status_bar.pack(side='bottom', fill='x')

# ===== МЕНЮ =====

menubar = tk.Menu(window)

# Меню "Файл"
file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Открыть аудио", command=open_audio_file)
file_menu.add_command(label="Открыть текст", command=open_text_file)
file_menu.add_separator()
file_menu.add_command(label="Выход", command=on_closing)
menubar.add_cascade(label="Файл", menu=file_menu)

# Меню "Справка"
help_menu = tk.Menu(menubar, tearoff=0)
help_menu.add_command(
    label="О программе", 
    command=lambda: messagebox.showinfo(
        "О программе", 
        "Whisper Audio to Text Converter\nВерсия 1.0\n\nПреобразует аудио в текст с помощью модели Whisper от OpenAI."
    )
)
menubar.add_cascade(label="Справка", menu=help_menu)

window.config(menu=menubar)

# Обработка закрытия окна
window.protocol("WM_DELETE_WINDOW", on_closing)

# Загружаем модель при старте
try:
    model = whisper.load_model(MODEL_PATH)
    status_bar.config(text="Модель загружена. Готов к работе.")
except:
    status_bar.config(text="Модель не найдена. Модель будет скачана при запуске транскрибирования")

# Запуск главного цикла
window.mainloop()