<?php

return [
    /*
     * Path to the receipt export used by TransactionImportSeeder, relative to the
     * application base path. Defaults to the repository's ML/data export so a local
     * `php artisan db:seed` works without extra setup.
     */
    'seed_csv' => env('MYVENTORY_SEED_CSV', '../ML/data/Transactions.csv'),
];
