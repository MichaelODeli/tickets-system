# tickers-system
Система тикетов для техподдержки пользователей, основанная на Dash.

## Будущие особенности
- Установка *в один клик* с помощью *docker*
- Четыре уровня доступа
    - *Пользователь* (отправка тикетов, просмотр статусов)
    - *Специалист поддержки* (прием тикетов, рассмотрение, отправка решений и предложений)
    - *Администратор приложения* (настройка системы)
    - *Аналитик* (просмотр статистики по тикетам)
- Настраиваемая форма для создания отчетов
- Личные кабинеты
- Привлечение сотрудников из других отделов для решения проблем
- Уведомления
- Комментарии

## Реализовано:
- Отправка тикетов пользователем без авторизации и получение идентификатора отчета в формате UUIDv7
- Просмотр полученных тикетов в виде списка на отдельной странице

## Полезные ссылки
- [CHANGELOG](./CHANGELOG.md)
- [Шаги разработки](./DEV_STEPS.md)