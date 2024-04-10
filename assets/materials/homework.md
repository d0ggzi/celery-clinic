[Вернуться][main]

---

[Ссылка][hw] на ДЗ в Github Classroom.

# Домашнее задание:

Цель задания - создать веб-приложение на Django (или другом фреймворке), которое будет использовать Celery для
выполнения асинхронных задач.

Представьте, что ваше веб-приложение предоставляет интерфейс для некой длительной операции (например, анализ данных,
работу с изображениями, отправку уведомлений и т.д.).

## Задачи:

1. Настройте проект Django для работы с Celery.
2. Создайте асинхронную задачу Celery, имитирующую длительную операцию (например, `time.sleep()` на 10 секунд).
3. Реализуйте Django view, который будет отправлять эту задачу на выполнение и моментально возвращать пользователю
   HTTP-ответ с подтверждением, что задача принята.
4. Реализуйте механизм, который позволит отслеживать статус задачи (например, через другой view, который возвращает
   текущий статус задачи по её ID).
5. Дополните ваше приложение функционалом, который позволит после завершения задачи сохранять результат её выполнения (
   например, создавать запись в базе данных).
6. Напишите unit-тесты, проверяющие функционал асинхронной задачи.

## Критерии оценки (максимум 10 баллов):

- **1 балл**: Настроенный проект Django.
- **1 балл**: Настройка Celery и успешная интеграция его с Django.
- **1 балл**: Контейнеризация сервиса с использованием Docker.
- **2 балла**: Реализация асинхронной задачи Celery, корректно выполненной с имитацией длительной операции.
- **1 балл**: Реализация Django view для отправки задачи в Celery.
- **1 балл**: Реализация механизма отслеживания статуса задачи Celery.
- **2 балла**: Реализация механизма для сохранения результата выполнения задачи после её завершения.
- **1 балл**: Наличие юнит-тестов, проверяющих ключевые функциональные аспекты работы с Celery.

## Дополнительные условия:

Приветствуется создание README файла с инструкциями по запуску проекта и тестов, а также описание того, как можно
проверить результаты работы приложения.

## Рекомендации:

- Качество кода в соответствии с PEP8.
- Наличие комментариев и документации к ключевым фрагментам кода.
- Корректность используемых методов и архитектурных решений.

---

[Вернуться][main]

[main]: ../../README.md "содержание"

[hw]: https://classroom.github.com/a/aMAUlB4v "ДЗ"