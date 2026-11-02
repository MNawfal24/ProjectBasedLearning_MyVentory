#!/bin/sh
set -e

cd /var/www/html

# storage is a named volume, so its directory tree is rebuilt on first run.
mkdir -p storage/framework/cache/data storage/framework/sessions storage/framework/views storage/logs storage/app bootstrap/cache
chown -R www-data:www-data storage bootstrap/cache

# A stable key is kept in storage so restarts do not invalidate sessions and cookies.
if [ -z "${APP_KEY:-}" ]; then
    if [ ! -s storage/app/app.key ]; then
        php artisan key:generate --show > storage/app/app.key
    fi
    APP_KEY="$(cat storage/app/app.key)"
    export APP_KEY
fi

if [ "${DB_CONNECTION:-pgsql}" = "pgsql" ]; then
    echo "Menunggu database ${DB_HOST:-db}:${DB_PORT:-5432}..."
    until php -r '
        try {
            new PDO(sprintf("pgsql:host=%s;port=%s;dbname=%s", getenv("DB_HOST") ?: "db", getenv("DB_PORT") ?: "5432", getenv("DB_DATABASE") ?: "myventory"), getenv("DB_USERNAME") ?: "myventory", getenv("DB_PASSWORD") ?: "");
            exit(0);
        } catch (Throwable $e) {
            exit(1);
        }
    ' 2>/dev/null; do
        sleep 2
    done
fi

php artisan migrate --force --no-interaction

if [ "${MYVENTORY_SEED:-true}" = "true" ]; then
    php artisan db:seed --force --no-interaction
fi

php artisan config:cache
php artisan route:cache

exec "$@"
