# Настройка Google OAuth для авторизации на сайте

## Шаг 1: Создайте проект в Google Cloud Console

1. Перейдите на [Google Cloud Console](https://console.cloud.google.com/)
2. Войдите в свой аккаунт Google
3. Нажмите на выпадающее меню в верхней панели и выберите "Новый проект"
4. Введите имя проекта, например "Mining Platform" и нажмите "Создать"
5. Подождите, пока проект создастся, и перейдите к нему

## Шаг 2: Настройте OAuth согласие

1. В боковом меню перейдите в "APIs & Services" > "OAuth consent screen"
2. Выберите тип пользователей для вашего приложения (External или Internal)
3. Нажмите "Create"
4. Заполните обязательные поля:
   - App name: "Mining Platform"
   - User support email: ваш email
   - Developer contact information: ваш email
5. Нажмите "Save and Continue"
6. На шаге "Scopes" добавьте следующие области:
   - email
   - profile
   - openid
7. Нажмите "Save and Continue"
8. На шаге "Test users" можете добавить тестовых пользователей или пропустить этот шаг
9. Нажмите "Save and Continue"
10. Проверьте информацию и нажмите "Back to Dashboard"

## Шаг 3: Создайте учетные данные OAuth

1. В боковом меню перейдите в "APIs & Services" > "Credentials"
2. Нажмите "Create Credentials" и выберите "OAuth client ID"
3. В качестве типа приложения выберите "Web application"
4. Введите имя, например "Mining Platform Web Client"
5. В разделе "Authorized JavaScript origins" добавьте:
   - http://localhost:5000 (для локальной разработки)
   - https://ваш-домен.com (для продакшн)
6. В разделе "Authorized redirect URIs" добавьте:
   - http://localhost:5000/auth/google/callback (для локальной разработки)
   - https://ваш-домен.com/auth/google/callback (для продакшн)
7. Нажмите "Create"
8. Вы получите Client ID и Client Secret

## Шаг 4: Настройте переменные окружения

Добавьте полученные ID и Secret в `.env` файл вашего проекта:

```
GOOGLE_CLIENT_ID=ваш-client-id
GOOGLE_CLIENT_SECRET=ваш-client-secret
GOOGLE_DISCOVERY_URL=https://accounts.google.com/.well-known/openid-configuration
```

## Шаг 5: Перезапустите приложение

После настройки всех параметров, перезапустите Flask-приложение, чтобы изменения вступили в силу.

## Проверка

После настройки вы можете проверить функциональность, нажав на кнопку "Login with Google" на странице входа. 