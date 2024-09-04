# Yandex.Tracker_changelogins

## Описание

Скрипт является **примером** переназначения пользователей Яндекс Трекер в задачах и меняет пользователей Cloud Organization на пользователей Яндекс 360 организации, параллельно подключенной в Трекер в следующих полях задач: "Автор", "Исполнитель", "Наблюдатели". Скрипт **не** переопределяет права очереди, доступ в Яндекс Формы, Вики. 

## Подготовка окружения

Для запуска скрипта необходимо:

- Получить ID Cloud Organization, которая привязана к Трекеру (bp******************)
- Выпустить токен сервисного приложения с правами tracker: read, tracker: write. Как получить токен (необходимо делать с учетной записи @yandex.ru администратора организации Cloud): https://yandex.cloud/ru/docs/tracker/concepts/access#section_about_OAuth.
- Заполнить файл sample.env полученными данными. Для дальнейшей работы файл необходимо переименовать в .env
- Подготовить виртуальное окружение (опционально): `python -m venv <название_виртуального_окружения>`. Подробнее про виртуальное окружение: https://docs.python.org/3/library/venv.html
- Установить зависимости, указанные в requirements.txt: `pip install -r requirements.txt`

## Запуск

Сценарий разделен на две части:
- Скрипт `mapping_users.py` делает запрос списка пользователей организации с помощью метода `get_users`. Полученный список пользователей переедается в `extract_users`, который обрабатывает полученный список, извлекает необходимые атрибуты пользователей и сортирует пользователей на два списка:
  - `cloud_users` - пользователи, которые состоят **только** в организации Cloud Organization;
  - `directory_users` - пользователи, которые состоят **только** в организации Yandex 360;
- В списки не попадут пользователи с учетными записями @yandex.ru, которые состоят в обеих организациях.
- В списках будут только пользователи с федеративными аккаунтами, которые "задвоились" в Трекере.
- Далее скрипт ищет совпадения в двух списках по полю `email`. Если в списках `cloud_users` и `directory_users` найдены совпадения по значению ключа `email`, то в файле `to.txt` будет произведена запись: `<Cloud_user_ID> <Yandex360_user_ID> #`. Если необходимо поменять местами ID - нужно закомментировать строку 64 и раскомментировать строку 63 в `mapping_users.py`
- После успешного завершения скрипта в директории появится файл `to.txt`
- Далее необходимо запустить скрипт `change_logins.py`. Будет выполнена замена пользователей в полях "Автор", "Исполнитель", "Наблюдатели" задач Трекера.