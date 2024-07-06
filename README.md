# Yandex.Tracker_changelogins



## Подготовка окружения

Для запуска скрипта необходимо:

- Получить ID Cloud Organization, которая привязана к Трекеру (bp******************)
- Выпустить токен сервисного приложения с правами tracker: read, tracker: write. Как получить токен (необходимо делать с учетной записи @yandex.ru администратора организации Cloud): https://yandex.cloud/ru/docs/tracker/concepts/access#section_about_OAuth.
- Заполнить файл sample.env полученными данными. Для дальнейшей работы файл необходимо переименовать в .env
- Подготовить виртуальное окружение (опционально): `python -m venv <название_виртуального_окружения>`. Подробнее про виртуальное окружение: https://docs.python.org/3/library/venv.html
- Установить зависимости, указанные в requirements.txt: `pip install requiremenets.txt`

## Запуск 