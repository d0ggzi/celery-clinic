[Вернуться][main]

---

# Асинхронная обработка с помощью Celery

Вы успешно собрали кусочки пазла, необходимые для выполнения асинхронных задач с помощью Django, Redis и Celery.
Но на данный момент вы еще не определили ни одной задачи, которую можно было бы передать Celery.

Ваш последний шаг по интеграции Celery с Django и передаче работы распределенной очереди задач Celery - это рефакторинг
функциональности отправки электронной почты в задачу Celery.

## Пересмотрите синхронный код

На данный момент ваш код определяет функциональность отправки электронной почты в `.send_email()` `FeedbackForm` в файле
`forms.py`:

```py
# feedback/forms.py

from time import sleep
from django.core.mail import send_mail
from django import forms


class FeedbackForm(forms.Form):
    email = forms.EmailField(label="Email")
    message = forms.CharField(
        label="Сообщение", widget=forms.Textarea(attrs={"rows": 5})
    )

    def send_email(self):
        """Sends an email when the feedback form has been submitted."""
        sleep(20)  # Simulate expensive operation(s) that freeze Django
        send_mail(
            "Твой отзыв",
            f"\t{self.cleaned_data['message']}\n\nСпасибо!",
            "support@example.com",
            [self.cleaned_data["email_address"]],
            fail_silently=False,
        )
```

Вы определяете `.send_email()` в строке 13. Метод имитирует дорогостоящую операцию, которая заморозит ваше приложение на
двадцать секунд, с помощью вызова `sleep()` в строке 15. В строках с 16 по 22 вы составляете письмо, которое будете
отправлять с помощью удобной функции Django `send_mail()`, которую вы импортировали в строке 4.

Вам также нужно вызывать `.send_email()` при успешном отправлении формы, и вы настраиваете это в `.form_valid()` из
`views.py`:

```py
# feedback/views.py

from feedback.forms import FeedbackForm
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateView


class FeedbackFormView(FormView):
    template_name = "feedback/feedback.html"
    form_class = FeedbackForm
    success_url = "/success/"

    def form_valid(self, form):
        form.send_email()
        return super().form_valid(form)


class SuccessView(TemplateView):
    template_name = "feedback/success.html"
```

В строке 12 определён метод `.form_valid()`, который `FeedbackFormView` автоматически вызывает при успешной отправке
формы. В строке 13 вы наконец-то вызываете `.send_email()`.

Ваша настройка работает, но из-за имитации дорогостоящей операции проходит слишком много времени, прежде чем ваше
приложение снова станет доступным и позволит пользователям продолжить просмотри и работу с ним. Пора это изменить,
позволив Celery выполнять отправку писем по собственному расписанию!

## Рефакторинг кода как задачи Celery

Чтобы `app.autodiscover_tasks()` работала так, как описано, вам нужно определить задачи Celery в отдельном модуле
`tasks.py` внутри каждого приложения вашего Django-проекта.

> Примечание: В этом примере у вас только одно приложение. В более крупных проектах Django, скорее всего, будет больше
> приложений. Если вы придерживаетесь стандартных настроек, то создайте файл tasks.py для каждого приложения и храните в
> нем задачи Celery.

Создайте новый файл `tasks.py` в приложении `feedback/`:

```
feedback/
│
├── migrations/
│   └── __init__.py
│
├── templates/
│   │
│   └── feedback/
│       ├── base.html
│       ├── feedback.html
│       └── success.html
│
├── __init__.py
├── admin.py
├── apps.py
├── forms.py
├── models.py
├── tasks.py
├── tests.py
├── urls.py
└── views.py
```

В этом файле вы определяете новую функцию, которая будет управлять логикой отправки электронной почты. Возьмите код из
`.send_mail()` в `forms.py` и используйте его в качестве основы для создания `send_feedback_email_task()` в `tasks.py`:

```py
# feedback/tasks.py

from time import sleep
from django.core.mail import send_mail


def send_feedback_email_task(email_address, message):
    """Sends an email when the feedback form has been submitted."""
    sleep(20)  # Simulate expensive operation(s) that freeze Django
    send_mail(
        "Твой отзыв",
        f"\t{message}\n\nnСпасибо!",
        "support@example.com",
        [email_address],
        fail_silently=False,
    )
```

Не забудьте добавить необходимые импорты, как показано в строках 3 и 4.

До сих пор вы в основном копировали код из `.send_mail()` в `send_feedback_email_task()`. Вы также немного изменили
определение функции, добавив два параметра в строке 6. Вы используете эти параметры в строках 11 и 13, чтобы заменить
значения, которые вы ранее извлекали из `.clean_data` в `.send_mail()`. Это изменение необходимо, потому что в новой
функции у вас нет доступа к этому атрибуту экземпляра.

В остальном `send_feedback_email_task()` выглядит так же, как и `.send_email()`. Celery еще даже не подключился!

Чтобы превратить эту функцию в задачу Celery, достаточно украсить ее атрибутом `@shared_task`, который вы импортируете
из
celery:

```py
# feedback/tasks.py

from time import sleep
from django.core.mail import send_mail
from celery import shared_task


@shared_task()
def send_feedback_email_task(email_address, message):
    """Sends an email when the feedback form has been submitted."""
    sleep(20)  # Simulate expensive operation(s) that freeze Django
    send_mail(
        "Your Feedback",
        f"\t{message}\n\nThank you!",
        "support@example.com",
        [email_address],
        fail_silently=False,
    )
```

Импортировав `shared_task()` из celery и украсив им `send_feedback_email_task()`, вы закончите с необходимыми
изменениями кода в этом файле.

Передача задачи в Celery вращается вокруг класса `Celery Task`, и вы можете создавать задачи, добавляя декораторы к
определениям ваших функций.

Если ваш продюсер - приложение Django, то вы захотите использовать декоратор `@shared_task` для создания задачи, что
позволит сохранить многоразовость ваших приложений.

С этими дополнениями вы закончили настройку асинхронной задачи в Celery. Вам останется только рефакторить, где и как
вызывать ее в коде вашего веб-приложения.

Вернитесь к файлу `forms.py`, откуда вы взяли код отправки электронной почты, и отрефакторьте `.send_email()` так, чтобы
он вызывал `send_feedback_email_task()`:

```py
# feedback/forms.py

# Removed: from time import sleep
# Removed: from django.core.mail import send_mail
from django import forms
from feedback.tasks import send_feedback_email_task


class FeedbackForm(forms.Form):
    email = forms.EmailField(label="Email")
    message = forms.CharField(
        label="Сообщение", widget=forms.Textarea(attrs={"rows": 5})
    )

    def send_email(self):
        send_feedback_email_task.delay(
            self.cleaned_data["email"],
            self.cleaned_data["message"],
        )
```

Вместо того чтобы обрабатывать логику кода отправки электронной почты в `.send_email()`, вы перенесли ее в
`send_feedback_email_task()` в `tasks.py`. Это изменение означает, что вы также можете удалить устаревшие операторы
импорта в строках 3 и 4.

Теперь вы импортируете `send_feedback_email_task()` из `feedback.tasks` в строке 6.

В строке 15 вы вызываете `.delay()` для `send_feedback_email_task()` и передаете ей данные отправленной формы,
извлеченные из `.clean_data`, в качестве аргументов в строке 16.

> Примечание: Вызов `.delay()` - это самый быстрый способ отправить сообщение о задаче в Celery. Этот метод является
> сокращением до более мощного `.apply_async(`), который дополнительно поддерживает опции выполнения для тонкой
> настройки сообщения задачи.
>
> При использовании `.apply_async()` ваш вызов для достижения того же, что и выше, будет немного более многословным:
>
> ```py
> send_feedback_email_task.apply_async(args=[
>         self.cleaned_data["email"],
>         self.cleaned_data["message"],
>     ]
> )
> ```
> Хотя `.delay()` является лучшим выбором для такого простого сообщения задачи, как это, вы выиграете от множества опций
> выполнения с `.apply_async()`, таких как обратный отсчет и повторная попытка.

Применив эти изменения в `tasks.py` и `forms.py`, вы закончили рефакторинг! Основная часть работы по запуску асинхронных
задач с помощью Django и Celery заключается в настройке, а не в коде, который вам нужно написать.

Но работает ли это?

## Протестируйте свою асинхронную задачу

Когда вы запускаете рабочий Celery, он загружает ваш код в память. Когда он получит задание через брокер сообщений, он
выполнит этот код. Из-за этого вам нужно перезапускать Celery worker каждый раз, когда вы меняете код.

> Примечание: Чтобы избежать ручного перезапуска рабочего Celery при каждом изменении кода во время разработки, вы
> можете настроить автозагрузку с помощью `watchdog` или написав собственную команду управления.

Вы создали задачу, о которой рабочий, запущенный ранее, не знает, поэтому вам нужно перезапустить его. Откройте окно
терминала, в котором запущен рабочий Celery, и остановите выполнение, нажав Ctrl+C.

Затем перезапустите рабочий с помощью той же команды, которую вы использовали ранее, и добавьте `-l info`, чтобы
установить уровень логирования на info:

```shell
python -m celery -A django_celery worker -l info
```

Установка флага `-l` в значение `info` означает, что вы увидите больше информации, выведенной на ваш терминал.
При запуске Celery отображает все задачи, которые он обнаружил, в разделе `[tasks]`:

```
[tasks]
  . feedback.tasks.send_feedback_email_task
```

Этот вывод подтверждает, что Celery зарегистрировал `send_feedback_email_task()` и готов обрабатывать входящие
сообщения, связанные с этой задачей.

Когда все службы запущены, а ваш код отрефакторен для Celery, вы готовы встать на место одного из своих пользователей и
протестировать руками свой отрефакторенный рабочий процесс.

Если теперь вы отправляете форму обратной связи на главной странице приложения, вы быстро перенаправляетесь на страницу
успеха. Ура! Не нужно ждать и расстраиваться. Вы даже можете вернуться к форме обратной связи и сразу же отправить еще
один отзыв.

Но что происходит под капотом? В синхронном примере вы видели, как сообщение появилось в окне терминала, в котором
вы запускали сервер разработки Django. В этот раз оно там не появляется - даже после того, как прошло двадцать секунд.

Вместо этого вы увидите, что текст письма появляется в окне терминала, где вы запускаете Celery, вместе с другими логами
о выполнении задачи:

```shell
[INFO/MainProcess] Task feedback.tasks.send_feedback_email_task[567b389b-4a2c-4b60-819b-6c068a42f1da] received
[WARNING/ForkPoolWorker-8] Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 8bit
Subject: =?utf-8?b?0KLQstC+0Lkg0L7RgtC30YvQsg==?=
From: support@example.com
To: test@test.test
Date: Wed, 25 Mar 2024 07:01:02 -0000
Message-ID: 
 <171149766242.1963.12176352829885086909@133.31.168.192.in-addr.arpa>

        Привет, Сельдерей!

Спасибо!
[WARNING/ForkPoolWorker-8] -------------------------------------------------------------------------------
[INFO/ForkPoolWorker-8] Task feedback.tasks.send_feedback_email_task[567b389b-4a2c-4b60-819b-6c068a42f1da] succeeded in 20.003958039997087s: None
```

Поскольку вы запустили Celery worker с уровнем логирования info (`-l info`), вы можете прочитать подробное описание
того, что происходит на стороне Celery.

Во-первых, вы можете заметить, что в логах сообщается о получении задачи `send_feedback_email_task`. Если вы посмотрите
это окно терминала сразу после отправки ответа на отзыв, то увидите, что этот лог печатается немедленно.

После этого Celery переходит в фазу ожидания, вызванную вызовом `sleep()`, который ранее заморозил ваше приложение
Django. В то время как вы можете продолжать использовать свое приложение Django немедленно, Celery выполняет
дорогостоящие вычисления за вас в фоновом режиме.

По истечении двадцати секунд Celery печатает в окне терминала фиктивное письмо, которое Django создает с помощью
`send_mail()`. Затем он добавляет еще одну запись в лог, которая сообщает, что `send_feedback_email_task` прошла
успешно, сколько времени это заняло (`20.003958039997087s`), и какое значение было возвращено (`None`).

> Примечание: Имейте в виду, что ваше приложение Django не будет знать, удалось ли выполнить задачу Celery в этом
> примере. Это означает, что сообщение "Спасибо!", которое увидит ваш читатель, не обязательно означает, что сообщение
> благополучно дошло до вас. Однако, поскольку вы создали базу данных с помощью Redis, вы можете запросить ее, чтобы
> определить, было ли выполнение задачи успешным или нет.
>
> Из-за того, как работает HTTP, информирование пользователя на UI об успешном завершении фоновой задачи -
> не самая простая задача. Для этого вам потребуется настроить WebSockets через Django Channels.

Все прошло отлично! Похоже, что ваш отзыв был отправлен быстро, и вам не пришлось сидеть в напряженном ожидании.

Отличная работа! Вы успешно интегрировали Celery в ваше Django-приложение и настроили его на обработку асинхронной
задачи. Теперь Celery обрабатывает отправку электронной почты и все ее накладные расходы в качестве фоновой задачи.
Отправка электронной почты не должна беспокоить ваше веб-приложение после того, как оно передало инструкции задачи в
распределенную очередь задач Celery.

---

[Вернуться][main]


[main]: ../../README.md "содержание"
