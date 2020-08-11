# Swagger Whats New (Backend)

#### Ссылка на рабочий проект (link to deployed project): 
[https://www.swagger-whats-new.com](https://www.swagger-whats-new.com)

#### Ссылка на репозиторий фронтенд части проекта (link to frontend app repository): 
[Swagger Whats New (Frontend)](https://github.com/pianoyeg94/swagger_whats_new_frontend)

#### Ссылка на Docker Hub репозиторий (link to Docker Hub repository): 
[Docker Hub repository](https://hub.docker.com/repository/docker/pianoyeg94/swagger_whats_new_backend)
<br />

## *Оглавление (Contents)*
| На русском                                                          | In English                                                               |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| [1. Краткое описание проекта](#short-description-rus)               | [1. High-level project overview](#short-description-eng)                 |
| [2. Используемые технологии](#used-tech-rus)                        | [2. Technologies used](#used-tech-eng)                                   |
| [3. Инструкция по запуску проекта локально](#instruction-rus)       | [3. Instruction on how to launch this project locally](#instruction-eng) |
| [4. Подробное описание возможностей проекта](#long-description-rus) | [4. Detailed project description](#long-description-eng)                 |
| [5. Планы по развитию проекта](#future-plans-rus)                   | [5. Future plans on developing this project](#future-plans-eng)          |
<br />
 
## <a name="short-description-rus">1. Краткое Описание проекта</a>
Серверная часть вэб приложения для команд разработки и тестирования, 
которое занимается отслеживанием истории изменений публичного интерфейса Rest API 
посредством интеграции с Open API (Swagger) и системами контроля версий 
(на данный момент поддерживаются интеграции с GitHub и Bitbucket).
<br />

## <a name="used-tech-rus">2. Используемые технологии</a>
 * Язык программирования - Python 3.8
 * Бэкэнд фрэймворк - Django + Django Rest Framework
 * Базы данных - Postgresql
 * Локальная разработка - Docker + Docker Compose, ngrok
 * Работа с отложенными/асинхронными и фоновыми задачами - Celery + Celery Beat + RabbitMQ
 * Мониторинг Celery воркеров и RabbitMQ - Flower, RabbitMQ Management UI
 * Юнит тесты - pytest, django-pytest
 * Деплой в "продакшн" - Google Kubernetes Engine
 * WSGI сервер в "продакшене" - Gunicorn + Nginx (в качестве reverse proxy и static/media file server) внутри Kubernetes кластера
 * Логирование в "продакшене" - Sentry
 * Фронтэнд технологии - Angular 9 + NgRx (Redux pattern), в "продакшене" используется Nginx в качестве static content server внутри Kubernetes кластера

## <a name="instruction-rus">3. Инструкция по запуску проекта локально</a>
1) Установить Docker + Docker Compose и ngrok (для работы с вэбхуками) на локальной машине
2) Склонировать репозиторий
3) Список аккаунтов, созданных специально для публичного тестирования:
   - Тестовая почта: swagger_whats_new_test@mail.ru, пароль - 97442746d8b511ea87d00242ac130003
   - Тестовый почтовый сервер, на котором можно проверить письма, отправляемые приложением: mailtrap.io, логин - swagger_whats_new_test@mail.ru, пароль -            97442746d8b511ea87d00242ac130003
   - Тестовый GitHub аккаунт для OAuth интеграции: логин - swagger-whats-new-test, пароль - 97442746d8b511ea87d00242ac130003
   - Тестовый Bitbucket аккаунт для OAuth интеграции: логин - swagger_whats_new_test@mail.ru, пароль - 97442746d8b511ea87d00242ac130003
4) Запустить ngrok на порту 8000, хост указать тот, на котором будет запущен Docker. Примеры команд: 
   - ngrok http http://localhost:8000 (Linux, Docker Desktop (Windows, MacOS)), 
   - ngrok http http://192.168.99.100:8000 (Docker Toolbox (Windows, адрес виртуальной машины), IP адрес может быть другой) 
5) Настроить переменные окружения (папка environments_examples, переименовать в environments): \
&nbsp;&nbsp;&nbsp;&nbsp; А) Файл ".env.dev":
<pre>   
      - SECRET_KEY - заполнить любым сгенерированным ключом
      - DJANGO_ALLOWED_HOSTS - заполнить двумя хостами: 
        -- на 1й позиции доменное имя, сгенерированное ngrok. Пример: f5fc73021ac9.ngrok.io 
        -- на 2й позиции хост, на котором будет запущен Docker. Примеры: localhost, 192.168.99.100
      - SQL_PASSWORD - любой пароль (такой же пароль надо будет указать в поле POSTGRES_PASSWORD в файле ".env.dev.db")
      - EMAIL_HOST_USER - 26902a5d1fd5f9 (mailtrap.io user)
      - EMAIL_HOST_PASSWORD - 1a35447ad1522c (mailtrap.io password)
      - GITHUB_CLIENT_ID - 16c0295bd6dea56dca7c
      - GITHUB_CLIENT_SECRET - 21942aa0cc5774cd3bc6549c92e19168b9925814
      - BITBUCKET_CLIENT_ID - K38gWzR46jPa5hwYkz  
      - BITBUCKET_CLIENT_SECRET - tZU47fPtr8hRjVct8X9QsEcjWecCFBwW
      - BROKER_PASSWORD - любой пароль
      - CORS_ORIGIN_WHITELIST - хост и порт, на котором будет локально запущено Angular приложение (скорее всего http://localhost:4200)
      - CLIENT_SITE_BASE_URL - хост и порт, на котором будет локально запущено Angular приложение (скорее всего http://localhost:4200) 
</pre> 
 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Б) Файл ".env.dev.db":
<pre>    
      - POSTGRES_PASSWORD - любой пароль (такой же пароль надо указать в поле SQL_PASSWORD в файле ".env.dev")
</pre>
6) Запустить команду из корневой папки: \
   docker-compose up -d --build
7) Порты, по которым можно получить доступ к контейнерам извне:
   - Django приложение - 8000 (root path для API начинается с /v1/)
   - Postgres - 5432
   - RabbitMQ Management UI - 15672
   - Flower - 8888
8) Команды для дальнейшей работы с проектом:
   - Приостановить работу контейнеров - docker-compose stop
   - Возобновить работу контейнеров - docker-compose start
   - "Уничтожить" контейнеры - docker-compose down
   - "Уничтожить" контейнеры и привязанные к ним volumes - docker-compose down -v
   - Запустить контейнеры "с нуля" без пересборки - docker-compose -up -d
   - Запустить контейнеры с очисткой всех данных в БД (кроме миграций) - FLUSH=true docker-compose -up -d
   - Запустить контейнеры "с нуля" с пересборкой - docker-compose up -d --build
   - "Интерактивные" логи - docker-compose logs -f --tail <"number of lines"> <"container name"> (web - django app, db, rabbitmq, celery, celery-beat, flower) 
9) Запуск юнит тестов - docker-compose exec web pytest
10) Дэв логи Django приложения пишутся в <корневая папка>/app/logs/dev.log 
11) Подробную инструкцию по локальному запуску "фронтовой" части проекта можно найти в репозитории [Swagger Whats New (Frontend)](https://github.com/pianoyeg94/swagger_whats_new_frontend)


## <a name="long-description-rus">4. Подробное описание возможностей проекта</a>
1) Работа с пользователями, регистрацией, аутентификаций и авторизацией (за это отвечает приложение "accounts"):
   - Для того, чтобы начать работу с приложением, необходимо создать компанию и владельца компании (создаются одновременно, проще всего сделать через UI)
   - Далее необходимо верифицировать свою почту, для того, чтобы иметь возможность приглашать других пользователей в свою компанию 
   (в случае локальной разработки письмо придет на mailtrap.io)
   - Далее идет перечисление основных возможностей auth системы: \
      -- приглашение пользователей в компанию c последующей регистрацией по ссылке \
      -- манипуляции с правами доступа пользователей \
      -- восстановление и изменение пароля \
      -- логин, логаут (jwt access and refresh tokens) \
      -- изменение учетных данных \
      -- удаление пользователей из компании (владельцем или самим пользователем)
2) Основной функционал проекта строится на интеграции и взаимодействии с системами контроля версий и Open API (за это отвечает приложение "swagger_projects"):
   - Основной единицей бизнес логики здесь является такая сущность, как Swagger Project
   - Swagger Project есть двух видов: не интегрированные с какой-либо системой контроля версий и интегрированные (более подробно ниже)
   - Главной функцией Swagger Project является отслеживание истории изменений любого Rest API, интегрированного с Swagger: \
      -- какие эндпоинты были добавлены/удалены \
      -- какие методы в каких-либо эндпоинтах были добавлены/удалены \
      -- какие поля в теле запроса или ответа были добавлены/удалены (отслеживает контракты и поля в этих контрактах)
   - При создании Swagger Project обязательно указывается url, по которому можно получить доступ к сваггер файлу в json формате (этот файл сохраняется в системе)
   - Посредством фоновых задач с некоторой периодичностью для каждого Swagger Project в системе происходит сравнение двух сваггер файлов: файл, хранящийся на данный момент в системе, и полученная по сети новая версия файла
   - Процесс сравнения файлов осуществляется конкуртено (много времени занимает получение нового файла по сети) и происходит за счет обхода двух json (parsed into dict) деревьев c последующим "прогоном" результатов через generator-based data pipeline для интерпретации и трансформации выходных данных. Результаты сохраняются в БД. Сравнение деревьев - credits to Fatih Erikli together with Invenio collaboration and their "dictdiffer" library (links: [PyPi](https://pypi.org/project/dictdiffer/) , [Documentation](https://dictdiffer.readthedocs.io/en/latest/))
   - Более подробно о Swagger Projects, интегрированных с системами контроля версий: \
      -- Интеграция приложения с системами контроля версий осуществляется через протокол OAuth \
      -- На данный момент поддерживаются две интеграции: GitHub и Bitbucket (планируется расширение списка интеграций) \
      -- Интеграция Swagger Projects c системами контроля версий сущесвтует главным образом для того, чтобы иметь возможность отслеживать, какой набор коммитов в ту или иную ветку репозитория повлек за собой изменения в Rest API \
      -- "Реагирование" на push события происходит посредством вэбхуков 
   - Также существует система комментирования пользователями истории изменений API на разных этапах 

## <a name="future-plans-rus">5. Планы по развитию проекта</a>
1) Новый функционал:
   - Добавить деление компаний на команды 
   - Интегрироваться с другими вендорами систем контроля версий: GitLab, Beanstalk, Mercurial
   - Добавить возможность единоразового сравнения сваггер файлов, посредством ручной загрузки двух файлов в систему (json, yaml)
   - Расширить систему фильтров
   - Добавить систему выгрузки отчетов по истории изменений Rest API
   - Добавить опциональную систему оповещений при обнаружении изменений в Rest API, привязанных к тому или иному Swagger Project: по почте, в слак
   - Добавить систему серверных оповещений клиентской стороны посредством вэбсокетов
2) Техническая сторона:
   - Перенести хранение файлов в "продакшене" с nfs серверов внутри кластера в blob buckets (Google Cloud или AWS S3). Возможно делегировать сам процесс аплоуда файлов на фронтенд, посредством использования presigned urls.
   - Делегировать работу с некоторыми отложенными задачами Celery воркерам, для того, чтобы уменьшить нагрузку на WSGI сервер (на данный момент большинство отложенных задач завязаны на сетевом взаимодействии и запускаются в отдельных потоках в рамках процесса gunicorn сервера)
   - При необходимости настроить систему кэширования с исползованием Redis. 
<br />

## <a name="short-description-eng">1. High-level project overview</a>
This is the server part of the Swagger Whats New application mainly targetting developer and QA teams. 
The primary goal of this application is to track the history of Rest API public interface changes 
via integrations with Open API (Swagger) and version control systems 
(currently GitHub and Bitbucket are supported).
<br />

## <a name="used-tech-eng">2. Technologies used</a>
 * Programming language - Python 3.8
 * Backend framework - Django + Django Rest Framework
 * Databases - Postgresql
 * Local development - Docker + Docker Compose, ngrok
 * Delayed/asynchronous and background tasks - Celery + Celery Beat + RabbitMQ
 * Celery worker and RabbitMQ monitoring - Flower, RabbitMQ Management UI
 * Unit testing - pytest, django-pytest
 * Deploying to "production" - Google Kubernetes Engine
 * WSGI server in "production" - Gunicorn + Nginx (as a reverse proxy and static/media file server) inside of a Kubernetes cluster
 * Logging in "production" - Sentry
 * Frontend technologies - Angular 9 + NgRx (Redux pattern), "production" - Nginx as a static content server inside of a Kubernetes cluster

## <a name="instruction-eng">3. Instruction on how to launch this project locally</a>
1) Download and install Docker + Docker Compose and ngrok (for webhooks) on your local machine
2) Clone this repository
3) List of accounts, created for public testing:
   - Test email address: swagger_whats_new_test@mail.ru, password - 97442746d8b511ea87d00242ac130003
   - Test mail server. Here you can check emails sent by the application: mailtrap.io, login - swagger_whats_new_test@mail.ru, password -            97442746d8b511ea87d00242ac130003
   - Test GitHub account for OAuth integration: login - swagger-whats-new-test, password - 97442746d8b511ea87d00242ac130003
   - Test Bitbucket account for OAuth integration: login - swagger_whats_new_test@mail.ru, password - 97442746d8b511ea87d00242ac130003
4) Launch ngrok on port 8000, host must be the same as your Docker host. Command examples: 
   - ngrok http http://localhost:8000 (Linux, Docker Desktop (Windows, MacOS)), 
   - ngrok http http://192.168.99.100:8000 (Docker Toolbox (Windows, VM address), exact IP address may be different) 
5) Configure environment variables ("environments_examples" directory, rename to "environments"): \
&nbsp;&nbsp;&nbsp;&nbsp; А) File ".env.dev":
<pre>   
      - SECRET_KEY - any randomly generated key
      - DJANGO_ALLOWED_HOSTS - specify 2 hosts: 
        -- 1st position, host generated by ngrok. Example: f5fc73021ac9.ngrok.io 
        -- 2nd position, Docker host. Example: localhost, 192.168.99.100
      - SQL_PASSWORD - any password (same password must be specified in the POSTGRES_PASSWORD field. File ".env.dev.db")
      - EMAIL_HOST_USER - 26902a5d1fd5f9 (mailtrap.io user)
      - EMAIL_HOST_PASSWORD - 1a35447ad1522c (mailtrap.io password)
      - GITHUB_CLIENT_ID - 16c0295bd6dea56dca7c
      - GITHUB_CLIENT_SECRET - 21942aa0cc5774cd3bc6549c92e19168b9925814
      - BITBUCKET_CLIENT_ID - K38gWzR46jPa5hwYkz  
      - BITBUCKET_CLIENT_SECRET - tZU47fPtr8hRjVct8X9QsEcjWecCFBwW
      - BROKER_PASSWORD - any password
      - CORS_ORIGIN_WHITELIST - host and port where your Angular app will be running (most likely http://localhost:4200)
      - CLIENT_SITE_BASE_URL - host and port where your Angular app will be running (most likely http://localhost:4200)
</pre> 
 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Б) Файл ".env.dev.db":
<pre>    
      - POSTGRES_PASSWORD - any password (same password must be specified in the SQL_PASSWORD field. File ".env.dev")
</pre>
6) Execute the following command from project's root directory: \
   docker-compose up -d --build
7) Ports for accessing docker containers:
   - Django application - 8000 (API root path begins with /v1/)
   - Postgres - 5432
   - RabbitMQ Management UI - 15672
   - Flower - 8888
8) Commands for managing the project:
   - Stop containers - docker-compose stop
   - Restart containers  - docker-compose start
   - Remove containers - docker-compose down
   - Remove containers and bound volumes - docker-compose down -v
   - Launch containers "from scratch" without rebuilding - docker-compose -up -d
   - Launch containers "from scratch" and wipe out database data (excluding migrations) - FLUSH=true docker-compose -up -d
   - Launch containers "from scratch" with rebuilding - docker-compose up -d --build
   - "Interactive" logs - docker-compose logs -f --tail <"number of lines"> <"container dns name"> (web - django app, db, rabbitmq, celery, celery-beat, flower) 
9) Command to run unit tests - docker-compose exec web pytest
10) Development Django app logs are written to this file: "root project directory"/app/logs/dev.log 
11) A complete instruction on how to launch the frontend part of the application you can find here: [Swagger Whats New (Frontend)](https://github.com/pianoyeg94/swagger_whats_new_frontend)

## <a name="long-description-eng">4. Detailed project description</a>
1) Registration, authentication and authorization system ("accounts" app):
   - To start working with the application, you need to register a company and company owner (created together in one go, easiest way to do it is via UI)
   - After that you have to verify your email address, or else you wan't be able to invite new members to your company 
   (while developing locally emails will be sent to mailtrap.io)
   - Other functionality provided by the auth system: \
      -- You can invite new users to your company, they will be registered with the help of a registration link \
      -- You can manipulate user premissions \
      -- You can reset and update your password \
      -- Login and logout (jwt access and refresh tokens) \
      -- You can edit your profile details and settings \
      -- You can delete users from your company (if you are a company owner or the same user)
2) The main functionality of this project is closely related to version control system and Open API integrations ("swagger_projects" app):
   - Main business logic entity - Swagger Project  
   - A Swagger Project can be a standalone entity integrated only with Open API or it can be also integrated with a version control system (more on this later)
   - The main responsibility of a Swagger Project is to track the history of Rest API changes, this Rest API must be integrated with Swagger: \
      -- tracks what enpoints were added/deleted \
      -- tracks what methods within an enpoint were added/deleted \
      -- tracks what fields in the request or response body were added/deleted (via tracking contracts and their fields)
   - When a Swagger Project is first created it is mandatory to specify a swagger file url, this way the system will have access to the current swagger file version at any point in time (the file is stored in the system)
   -  Every so often a background task is scheduled that compares 2 swagger files for every Swagger Project: file currently stored in the system and the new swagger file version pulled from the web
   - Search for swagger file differences is performed concurrently (most of the time workers are blocked on I/O). This is achieved by traversing and comparing 2 json trees (parsed into dicts). Output results are run through a generator-based data pipeline to interprate and transform the resulting data. Results are persisted to DB. Comparing trees - credits to Fatih Erikli together with Invenio collaboration and their "dictdiffer" library (links: [PyPi](https://pypi.org/project/dictdiffer/) , [Documentation](https://dictdiffer.readthedocs.io/en/latest/))
   - More details on integrating Swagger Projects with version control systems: \
      -- Integration is achieved via the OAuth protocol \
      -- Currently 2 integrations are supported: GitHub and Bitbucket (there are plans to add a bunch of other integrations) \
      -- The main reason for integrating Swagger Projects with version control systems is so that there is a mechanism to track, what commits triggered particular Rest API changes \
      -- Push events to specified repository branches are tracked via webhooks 
   - There is also a comment system associated with each swagger file change 

## <a name="future-plans-eng">5. Future plans on developing this project</a>
1) New functionality:
   - Add teams support, companies will be devided into teams 
   - Integrate with other version control system vendors: GitLab, Beanstalk, Mercurial
   - Add the ability to compare 2 swagger files as a 1 time activity only, user just needs to upload 2 swagger files and the system will find the differences if any (json, yaml)
   - Expand on the existing filtering system
   - Add support for Rest API changes history report download
   - Add an optional notification system activated when Rest API changes for a Swagger Project are registered: email, slack
   - Add server side notifications via websockets
2) Technical part:
   - Migrate file storage in "production": currently nfs server Kubernetes pods are used, needs to be transfered to blob buckets (Google Cloud or AWS S3). Maybe the whole process of uploading files will be delegated to the frontend part of the application, with the help of presigned urls.
   - Delegate most of the asynchronous task processing to Celery workers, the goal is to free up WSGI server's resources (currently most of the delayed tasks are I/O bound and processed in separate threads within Gunicorn's process)
   - Add Redis caching if necessary

