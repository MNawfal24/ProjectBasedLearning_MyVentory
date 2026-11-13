# MyVentory web dashboard: Laravel + Vue, served by Apache with mod_php.
# Build from the repository root so the Dockerfile can reach Web/ and the CSV:
#   docker build -f Docker/web/Dockerfile -t myventory-web .
#
# Stages:
#   assets  - builds the Vite bundle
#   runtime - production image (no dev dependencies)
#   testing - same image plus dev dependencies, used by `docker compose run test`

FROM node:22-alpine AS assets
WORKDIR /app
COPY Web/package.json Web/package-lock.json ./
RUN npm ci
COPY Web/vite.config.js ./
COPY Web/resources ./resources
COPY Web/public ./public
RUN npm run build

FROM php:8.4-apache AS base

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev unzip \
    && docker-php-ext-install pdo_pgsql opcache \
    && a2enmod rewrite headers \
    && rm -rf /var/lib/apt/lists/*

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

ENV APACHE_DOCUMENT_ROOT=/var/www/html/public \
    COMPOSER_ALLOW_SUPERUSER=1 \
    MYVENTORY_SEED=true

RUN sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/sites-available/*.conf \
    && sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf

COPY Docker/web/apache.conf /etc/apache2/conf-enabled/myventory.conf

WORKDIR /var/www/html

# Dependencies first so editing application code does not invalidate the vendor layer.
COPY Web/composer.json Web/composer.lock ./

FROM base AS runtime
RUN composer install --no-dev --no-interaction --prefer-dist --no-scripts --no-autoloader
COPY Web/ .
COPY --from=assets /app/public/build ./public/build
# Seed sources for the real dataset: receipts, stock ledger and item master.
# The directory copy keeps the build working when Stock.csv is not committed yet.
COPY ML/data/ ./database/data/
RUN composer dump-autoload --optimize --no-dev \
    && php artisan package:discover --ansi \
    && mkdir -p storage/framework/cache/data storage/framework/sessions storage/framework/views storage/logs bootstrap/cache \
    && chown -R www-data:www-data storage bootstrap/cache \
    && chmod -R a+rX /var/www/html
COPY Docker/web/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD php -r "exit(@file_get_contents('http://127.0.0.1/up') ? 0 : 1);"

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["apache2-foreground"]

FROM base AS testing
RUN composer install --no-interaction --prefer-dist --no-scripts --no-autoloader
COPY Web/ .
# The root Blade template calls @vite, so the tests need a manifest to render pages.
COPY --from=assets /app/public/build ./public/build
# Dotenv reads .env on every boot; an empty file keeps PHPUnit from reporting its absence.
RUN touch .env \
    && composer dump-autoload --optimize \
    && php artisan package:discover --ansi \
    && mkdir -p storage/framework/cache/data storage/framework/sessions storage/framework/views storage/logs bootstrap/cache
CMD ["php", "artisan", "test"]

