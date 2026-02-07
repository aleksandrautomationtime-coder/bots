# Бот: YouTube транскрипт + парсинг Telegram-каналов

Одна папка со всем нужным для бота. Команды: **/yt** (транскрипт YouTube), **/tg** (посты канала по ссылке).

## Локальный запуск

```bash
cd bot_upload
pip install -r requirements.txt
```

Создайте файл `.env` с токеном (скопируйте `.env.example`):

```
BOT_TOKEN=ваш_токен_от_BotFather
```

Запуск:

```bash
python bot.py
```

---

## Как выложить только эту папку на GitHub

Ты загружаешь **только папку `bot_upload`** — без всего «Сайт КаркасДом».

### Вариант 1: через сайт GitHub (без Git в системе)

1. На [github.com](https://github.com) нажми **+** → **New repository**.
2. Имя репозитория — например `yt-tg-bot`. Создай репозиторий (можно без README).
3. На странице репозитория нажми **uploading an existing file** (или **Add file** → **Upload files**).
4. Открой на компьютере папку **bot_upload** и перетащи в окно браузера **все файлы из неё**:
   - `bot.py`
   - `config.py`
   - `transcript.py`
   - `parse_channel.py`
   - `requirements.txt`
   - `.env.example`
   - `README.md`
   - `.gitignore` (если не виден — включи показ скрытых файлов в проводнике).
5. **Не загружай файл `.env`** — в нём токен, он не должен попадать на GitHub.
6. Нажми **Commit changes**.

Готово: в репозитории только бот.

### Вариант 2: через Git (из папки bot_upload)

1. Установи [Git](https://git-scm.com), если ещё нет.
2. Открой терминал и перейди в папку бота:

   ```bash
   cd "d:\Сайт КаркасДом\bot_upload"
   ```

3. Инициализация и первый коммит:

   ```bash
   git init
   git add .
   git commit -m "Бот: yt + tg"
   ```

4. На GitHub создай **новый пустой репозиторий** (без README и .gitignore).
5. Подключи его и отправь код (подставь свой логин и имя репо):

   ```bash
   git remote add origin https://github.com/ТВОЙ_ЛОГИН/ИМЯ_РЕПОЗИТОРИЯ.git
   git branch -M main
   git push -u origin main
   ```

Файл `.env` в репозиторий не попадёт — он указан в `.gitignore`.

### Деплой на Railway (или другой хостинг)

- В Railway: **New Project** → **Deploy from GitHub repo** → выбери этот репозиторий.
- **Root Directory** оставь пустым (в репо только файлы бота).
- В настройках сервиса добавь переменную **BOT_TOKEN**.
- Команда запуска: `python bot.py` (Railway обычно подхватывает сама).

Всё необходимое для бота лежит в этой одной папке.
