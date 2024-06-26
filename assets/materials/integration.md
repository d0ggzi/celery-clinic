[Вернуться][main]

---

# Интеграция Celery с Django

Теперь, когда вы знаете, что такое Celery и как он может помочь улучшить производительность вашего веб-приложения,
пришло время интегрировать его, чтобы вы могли запускать асинхронные задачи с помощью Celery.

Вы сосредоточитесь на интеграции Celery в существующий проект Django. Вы начнете с урезанного Django-приложения с
минимальным сценарием использования: сбор отзывов пользователей и отправка электронного письма в качестве ответа.

## Настройка приложения для обратной связи

Структура проекта:

```
source_code_initial/
│
├── django_celery/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── feedback/
│   │
│   ├── migrations/
│   │   └── __init__.py
│   │
│   ├── templates/
│   │   │
│   │   └── feedback/
│   │       ├── base.html
│   │       ├── feedback.html
│   │       └── success.html
│   │
│   │
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── .gitignore
├── manage.py
└── requirements.txt
```

Убедитесь, что вы находитесь внутри `source_code_initial/`, затем создайте и активируйте виртуальное окружение:

```shell
python3 -m venv venv
source venv/bin/activate
```

Когда виртуальное окружение будет активировано - можно установить Django:

```shell
pip install django
```

Завершите локальную настройку приложения Django, применив миграции и запустив сервер разработки:

```shell
python manage.py migrate
python manage.py runserver
```

Теперь вы можете открыть браузер и перейти на главную страницу приложения по адресу http://localhost:8000, где вас
встретит форма обратной связи:

![img.png](img.png)

Если попробовать заполнить и отправить форму, увидим результат:

![img_1.png](img_1.png)

Но есть проблема...

После нажатия кнопки "Отправить" приложение замирает. Вы можете видеть, как на вкладке браузера крутится маленькую
иконку спиннера, но страница не реагирует, и вы все еще видите всю информацию, которую ввели в форму.

Django требуется слишком много времени, чтобы обработать форму и перенаправить вас на следующую страницу!

Django замирает, потому что ему нужно синхронно обработать запрос на отправку электронной почты, прежде чем приступить к
решению следующей задачи - перенаправлению пользователя на страницу успеха.

Причина столь длительного замирания кроется в хитроумном вызове `time.sleep()` в `.send_email()`, который имитирует
трудоемкую задачу, связанную с отправкой электронной почты.

Конечно, в реальном приложении вы не стали бы добавлять в свой код временных задержек, заставляя Django спать.
Однако, какой бы почтовый сервис вы ни использовали, он, к сожалению, будет вносить некоторые задержки. Особенно
когда ваше приложение начнет обслуживать много пользователей, вы быстро столкнетесь с ограничениями.

> Примечание: Можно заменить вызов `time.sleep()` на любой трудоёмкий процесс, который необходимо выполнить в вашем
> веб-приложении для обслуживания пользователей.

Ваше приложение Django не должно обрабатывать длительные задачи синхронно, потому что это ухудшает пользовательский опыт
и общую полезность вашего приложения.

Вместо этого вы узнаете, как передать эту задачу воркеру Celery. Рабочие Celery могут выполнять вычисления в фоновом
режиме и позволять вашим пользователям спокойно просматривать ваше замечательное веб-приложение.

## Установка Celery в качестве очереди задач

Теперь, когда вы настроили приложение обратной связи и почувствовали задержку, возникающую при отправке электронной
почты, вы собираетесь улучшить пользовательский опыт.

Первым шагом в интеграции Celery в ваше приложение Django будет установка пакета Celery в ваше виртуальное окружение:

```shell
pip install celery
```

Однако просто установить Celery недостаточно. Если вы попытаетесь запустить очередь задач, вы заметите, что Celery
сначала вроде бы запускается нормально...

```shell
python -m celery worker
```

но затем выдаёт сообщение об ошибке, которое указывает, что Celery не может найти брокер сообщений:

```
[2024-03-27 00:53:59,983: ERROR/MainProcess] consumer: Cannot connect to amqp://guest:**@127.0.0.1:5672//: [Errno 61] Connection refused.
Trying again in 2.00 seconds... (1/100)
```

Celery нужен брокер сообщений для связи с программами, которые отправляют задания в очередь задач. Без брокера Celery не
может получать инструкции, поэтому он постоянно пытается переподключиться.

> Примечание: Вы можете заметить URL-подобный синтаксис в таргете, к которому Celery пытается подключиться. Название
> протокола, `amqp`, расшифровывается как `Advanced Message Queuing Protocol` и является протоколом обмена сообщениями,
> который использует Celery. Самым известным проектом, реализующим AMQP нативно, является RabbitMQ, но Redis также может
> взаимодействовать по этому протоколу.

Прежде чем использовать Celery, нужно установить брокер сообщений и определить проект в качестве производителя
сообщений. В вашем случае производителем будет ваше приложение Django, а брокером сообщений - Redis.

## Установка Redis в качестве брокера Celery и базы данных

Вам нужен брокер сообщений, чтобы Celery мог взаимодействовать с производителем задач (producer).
Вы будете использовать Redis, потому что Redis может служить одновременно и брокером сообщений, и базой данных.

Установка Redis:

```shell
brew install redis
```

После завершения установки вы можете запустить сервер Redis, чтобы убедиться, что все работает. Откройте новое окно
терминала, чтобы запустить сервер:

```shell
redis-server
```

> Примечание: Запуск redis-server запускает сервер Redis. Вы запускаете Redis как процесс, независимый от Python,
> поэтому вам не нужно активировать виртуальную среду при его запуске.

После запуска redis-server в вашем терминале появится логотип Redis в виде ASCII-рисунка, а также несколько сообщений
лога запуска. Последнее сообщение лога сообщит вам, что Redis готов принимать соединения.

Чтобы проверить, работает ли связь с сервером Redis, запустите Redis CLI в другом новом окне терминала:

```shell
redis-cli
```

В окно ввода вы можете ввести `ping` и нажать `Enter`, а затем дождаться ответа от Redis:

```shell
127.0.0.1:6379> ping
PONG
127.0.0.1:6379> 
```

Запустив Redis CLI с помощью redis-cli, вы отправили слово ping на сервер Redis, который ответил авторитетным PONG. Если
вы получили такой ответ, значит, установка Redis прошла успешно, и Celery сможет взаимодействовать с Redis.

Выйдите из Redis CLI, нажав Ctrl+C, прежде чем переходить к следующему шагу.

Далее вам понадобится Python-клиент для взаимодействия с Redis. Убедитесь, что вы находитесь в окне терминала, где ваша
виртуальная среда все еще активна, а затем установите redis-py:

```shell
pip install redis
```

Эта команда не устанавливает Redis на вашу систему, а только предоставляет интерфейс Python для подключения к Redis.

> Примечание: Вам нужно будет установить Redis на вашу систему и redis-py в виртуальную среду Python, чтобы вы могли
> работать с Redis из ваших программ на Python.

После завершения обеих установок вы успешно настроили брокер сообщений. Однако вы еще не подключили своего производителя
к Celery.

Если вы попытаетесь запустить Celery сейчас и включите имя приложения-продюсера, передав флаг `-A` вместе с именем
вашего приложения Django (django_celery):

```shell
python -m celery -A django_celery worker
```

... вы столкнетесь с еще одной ошибкой:

```shell
Error: Invalid value for '-A' / '--app': 
Unable to load celery application.
Module 'django_celery' has no attribute 'celery'
```

Пока что ваша распределенная очередь задач не может получать сообщения от вашего Django-приложения, потому что в вашем
Django-проекте не установлено приложение Celery.

## Добавление Celery в проект Django

Последний кусочек пазла - подключение приложения Django в качестве производителя сообщений к вашей очереди задач.

Перейдите в директорию `django_celery` и создайте новый файл `celery.py`:

```
django_celery/
├── __init__.py
├── asgi.py
├── celery.py
├── settings.py
├── urls.py
└── wsgi.py
```

Celery рекомендует использовать этот модуль для определения экземпляра приложения Celery. Откройте файл в IDE и добавьте
необходимый код:

```py
# django_celery/celery.py

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_celery.settings")
app = Celery("django_celery")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

Вам нужно лишь добавить в файл эти несколько строк кода. Подробнее:

- **Строка 3:** Вы импортируете встроенный модуль os, с которым вы, вероятно, знакомы по работе с файлами. Вы будете
  использовать его в строке 6, чтобы установить переменную окружения.
- **Строка 4:** Вы импортируете Celery из пакета celery. Вы используете его в строке 7 для создания экземпляра
  приложения Celery.
- **Строка 6:** Вы используете `.setdefault()` из `os.environ`, чтобы убедиться, что модуль `settings.py` вашего проекта
  Django доступен через ключ `DJANGO_SETTINGS_MODULE`.
- **Строка 7:** Вы создаете экземпляр приложения Celery и указываете в качестве аргумента имя главного модуля. В
  контексте вашего Django-приложения главным модулем является приложение Django, содержащее `celery.py`, поэтому вы
  передаете `django_celery`.
- **Строка 8:** Вы определяете файл настроек Django как конфигурационный файл для Celery и предоставляете пространство
  имен `CELERY`. Вам нужно будет добавить значение пространства имен, за которым следует знак подчеркивания `_`, к
  каждой переменной конфигурации, связанной с Celery. Вы могли бы определить другой файл настроек, но сохранение
  конфигурации Celery в файле настроек Django позволяет вам придерживаться единого центрального места для конфигураций.
- **Строка 9:** Вы указываете экземпляру приложения Celery автоматически находить все задачи в каждом приложении вашего
  Django-проекта. Это работает до тех пор, пока вы придерживаетесь структуры многоразовых приложений и определяете все
  задачи Celery для приложения в специальном модуле `tasks.py`. Вы создадите и заполните этот файл для вашего приложения
  `django_celery`, когда будете рефакторить код отправки писем позже.

Установив `celery.py` и попытавшись получить необходимые настройки Celery из файла `settings.py`, вы перейдете к
`settings.py`, чтобы добавить эти записи в нижнюю часть файла:

```py
# django_celery/settings.py

# ...

# Celery settings
CELERY_BROKER_URL = "redis://localhost:6379"
CELERY_RESULT_BACKEND = "redis://localhost:6379"
```

Эти две записи дают экземпляру приложения Celery достаточно информации, чтобы знать, куда отправлять сообщения и куда
записывать результаты. Поскольку вы используете Redis в качестве брокера сообщений и базы данных, оба URL-адреса
указывают на один и тот же адрес.

> Примечание: Эти URL-адреса могут также указывать на различные серверы и сервисы. Например, вы можете использовать
> RabbitMQ в качестве брокера сообщений и Redis в качестве бэк-энда результатов:
>
> ```py
> CELERY_BROKER_URL = "amqp://my_user:my_pass@localhost:5672/my_host"
> CELERY_RESULT_BACKEND = "redis://localhost:6379"
> ```
>
> Когда вы запустите свое приложение в прод, вы замените эти URL на продакшн местоположения каждого сервиса.

Обратите внимание на пространство имен CELERY_ в начале этих переменных настройки. Его нужно добавить из-за аргумента
namespace="CELERY", который вы передали в app.config_from_object() в строке 8 celery.py.

На этом этапе вы почти закончили интеграцию Celery в ваше веб-приложение. Осталось добавить последний элемент в
`__init__.py` вашего приложения управления:

```
django_celery/
├── __init__.py
├── asgi.py
├── celery.py
├── settings.py
├── urls.py
└── wsgi.py
```

Откройте файл в редакторе. В проекте Django по умолчанию каждая директория имеет файл `__init__.py`, который
помогает пометить ее как модуль. По умолчанию файл пуст, но вы можете добавить код, чтобы повлиять на поведение импорта.

Чтобы убедиться, что ваше приложение Celery загружается при запуске Django, вы должны добавить его в `__all__`:

```py
# django_celery/__init__.py

from .celery import app as celery_app

__all__ = ("celery_app",)
```

Загрузка приложения Celery при запуске Django гарантирует, что декоратор `@shared_task` будет использовать его
правильно.
Подробнее о `@shared_task` вы узнаете в следующем разделе.

Пора протестировать вашу настройку! Помните, что процесс, который вы настраиваете, требует одновременного запуска как
минимум трех сервисов:

1. Производитель (Producer): Ваше приложение Django
2. Брокер сообщений (Message Broker): Сервер Redis
3. Потребитель (Consumer): Ваше приложение Celery

Поскольку вы используете Redis, вы получите бэк-энд базы данных в качестве бонуса без запуска другого сервиса.

Откройте три отдельных окна терминала и запустите все программы, если они еще не запущены.

В первом окне запустите ваше веб-приложение на сервере разработки Django:

```shell
python manage.py runserver
```

Затем запустите сервер Redis во втором окне терминала, если вы остановили его ранее:

```shell
redis-server
```

Команда redis-server - единственная из трех команд, которую можно выполнить вне виртуального окружения, поэтому
убедитесь, что в двух других окнах терминала активно виртуальное окружение.

> Примечание: Вы можете получить ошибку, если сервер Redis все еще работает в фоновом режиме. В этом случае вам нужно
> будет вызвать SHUTDOWN перед выполнением redis-server.

Наконец, теперь вы можете корректно запустить Celery, не столкнувшись с сообщением об ошибке:

```shell
python -m celery -A django_celery worker
```

Запуская Celery с помощью этой команды, вы указываете после флага `-A` имя модуля, содержащего экземпляр вашего
приложения Celery, `django_celery`.

> Примечание: Хотя сообщение об ошибке, которое вы видели при запуске Celery до установки Redis, исчезло, вы все еще
> можете увидеть предупреждение, связанное с настройкой DEBUG в Django. Вы можете проигнорировать это предупреждение для
> данного примера, но вы всегда должны устанавливать значение DEBUG на False перед развертыванием сайта в производство.

В общем, вам нужно только добавить код в три упомянутых файла, чтобы интегрировать Celery в ваше приложение Django и
подготовить его к обработке асинхронных задач. Когда базовая настройка завершена, вы готовы написать задачу, которую
можно передать Celery.

В следующем разделе вы рефакторите `.send_email()`, чтобы вызвать асинхронную задачу Celery вместо того, чтобы
обрабатывать отправку электронной почты синхронно в Django.

---

[Вернуться][main]


[main]: ../../README.md "содержание"
