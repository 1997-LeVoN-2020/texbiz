---
name: package-for-deploy
description: Пересобрать сайт ТЕХБИЗ и упаковать texbiz-site.zip / texbiz-pyapp.zip для загрузки на хостинг (reg.ru, ISPmanager). Использовать когда просят "собери архивы для деплоя", "подготовь zip для загрузки на хостинг".
---

## Команда

```
python build.py
python -c "
import zipfile, os
def zip_dir(src, out):
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(src):
            for f in files:
                full = os.path.join(root, f)
                zf.write(full, os.path.relpath(full, src))
zip_dir('dist', 'texbiz-site.zip')
zip_dir('src/pyapp', 'texbiz-pyapp.zip')
"
```

Оба архива в `.gitignore`, в git не коммитятся.

## Куда что распаковывать (важно для этого хостинга)

- **`texbiz-site.zip`** (содержимое `dist/`, без обёрточной папки) → напрямую в директорию домена в ISPmanager (`/var/www/<пользователь>/data/www/tex-biz.ru`).
- **`texbiz-pyapp.zip`** (содержимое `src/pyapp/`) → в подпапку `mailapp/` **внутри той же** директории домена — на этом тарифе отдельной директории для Python-приложений нет, поэтому статика и Python-приложение физически лежат в одном корне (см. README, раздел «2. Python-приложение для формы»).

## После загрузки

Свериться, что `MAIL_ENDPOINT` в `src/static/script.js` (по умолчанию `/mailapp/send`) совпадает с реальным путём Python-приложения, настроенным в ISPmanager. Если путь другой — поменять константу в `script.js` и пересобрать (`python build.py`), затем перезалить `dist/script.js`.
