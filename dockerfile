# Используем официальный образ Python 3.9
FROM python:3.9-slim

# Создаем рабочую директорию
WORKDIR /app

# Копируем все файлы проекта (включая папки `images/` и `data.json`)
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем бота при старте контейнера
CMD ["python", "main.py"]