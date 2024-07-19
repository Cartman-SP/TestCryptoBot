# Используем официальный образ Python как базовый
FROM python:3.11

COPY requirements.txt .
COPY main.py api.py config.py .

# Устанавливаем зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Определяем команду для запуска приложения
CMD ["python", "./main.py"]
