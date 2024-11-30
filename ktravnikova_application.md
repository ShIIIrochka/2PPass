# Ксения Травникова - "2PPass"   
### Группа: 10 - И - 4
### Электронная почта: kdtravnikova@edu.hse.ru
### Tg: @shiro4k


**[НАЗВАНИЕ ПРОЕКТА]**

"2PPass - self-hosted менеджер паролей"

**[ ПРОБЛЕМНОЕ ПОЛЕ ]**   
С увеличением числа пользователей и организаций, требующих безопасного хранения и управления паролями, возникает необходимость в разработке эффективных и надежных отечественных решений для управления доступом к конфиденциальной информации. Современные менеджеры паролей часто сталкиваются с рядом проблем, включая:   
1. отсутствие гибкой системы группировки пользователей и распределения прав доступа,   
2. недостаточную защиту личных и общих паролей,   
3. сложность в управлении доступом для администраторов.

В существующих решениях наблюдаются следующие недостатки:   
1. отсутствие возможности создания кастомизированных групп пользователей с различными уровнями доступа,   
2. недостаточная поддержка для совместного использования паролей между несколькими пользователями,   
3. отсутствие функций для аудита и мониторинга доступа к паролямю. 


**[ ЗАКАЗЧИК / ПОТЕНЦИАЛЬНАЯ АУДИТОРИЯ ]**  
Разрабатываемый менеджер паролей может заинтересовать широкий круг организаций и пользователей, поскольку предназначен для обеспечения безопасного хранения и управления паролями. Однако необходимо выделить несколько ключевых групп пользователей, для которых предусмотрены специфические настройки и функционал. Эти настройки будут влиять на интерфейс, уровень доступа и возможности управления паролями. К выделяемым группам относятся:   
- Корпоративные пользователи (сотрудники компаний)   
- Администраторы IT-отделов   
- Менеджеры по безопасности информации   
- Малые и средние предприятия   
- Образовательные учреждения   


**[ АППАРАТНЫЕ / ПРОГРАММНЫЕ ТРЕБОВАНИЯ ]**   
* Docker 20+
* Docker-compose 3+
* ОЗУ: 4гб
* ПЗУ: от 10гб
* ОС: Linux 6.10.3+ x86_64 GNU/Linux



**[ ФУНКЦИОНАЛЬНЫЕ ТРЕБОВАНИЯ ]**  
Разрабатываемый менеджер паролей с self-hosted моделью обеспечит надежную защиту чувствительных данных, интуитивно понятный интерфейс для администраторов и пользователей, а также гибкую систему управления доступом, что значительно повысит уровень безопасности и удобства в использовании. Будут предоставлены следующие возможности:
* Создание и управление учетными записями пользователей с возможностью настройки индивидуальных параметров
* Хранение, генерирование, шеринг паролями
* Объединение пользователей в группы с различными уровнями доступа и правами
* Логгирование действий пользователей для обеспечения аудита и безопасности
* Выдача и управление правами доступа к паролям и другим ресурсам на основе ролей и групп


**[ ПОХОЖИЕ / АНАЛОГИЧНЫЕ ПРОДУКТЫ ]**   
Анализ 3 программных продуктов, которые максимально приближены к заданному функционалу, показал, что:  
* LastPass: не является self-hosted решением, что может быть менее безопасно для корпораций, имеет ограниченные возможности для кастомизации групп пользователей и распределения прав доступа.

* Bitwarden: ограничен в области аудита и логгирования действий.

* KeePass: не имеет встроенных функций для совместного использования паролей между пользователями и требует дополнительных усилий для настройки группового доступа и управления правами, что может усложнить его использование в корпоративной среде.


**[ ИНСТРУМЕНТЫ РАЗРАБОТКИ, ИНФОРМАЦИЯ О БД ]**  
* Python / FastAPI / Strawberry/ SQLModel - backend
* FastUI - frontend
* PostgeSQL or MongoDB - database

**[ ЭТАПЫ РАЗРАБОТКИ ]**  
* Разработка пользовательских сценариев
* Проэктирование архитектуры
* Разработка моделей
* Разработка сервисов приложения
* Разработка API
* Разработка пользовательского интерфейса с FastUI
* Тестирование, отладка
* Подготовка проекта к защите

**[ ВОЗМОЖНЫЕ РИСКИ ]**  
* Невозможность спроектировать удобный пользовательский интерфейс
* Невозможность обеспечить высокий уровень безопасности данных, что может привести к утечкам конфиденциальной информации
* Трудности с интеграцией системы управления доступом и правами пользователей, что может ограничить функциональность и гибкость продукта