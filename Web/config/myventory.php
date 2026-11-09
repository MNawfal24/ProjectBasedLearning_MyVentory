<?php

return [
    /*
     * Path to the receipt export used by TransactionImportSeeder, relative to the
     * application base path. Defaults to the repository's ML/data export so a local
     * `php artisan db:seed` works without extra setup.
     */
    'seed_csv' => env('MYVENTORY_SEED_CSV', '../ML/data/Transactions.csv'),

    /*
     * Real stock ledger and its ItemID mapping, also relative to the base path.
     * StockImportSeeder skips cleanly when the ledger is absent.
     */
    'stock_csv' => env('MYVENTORY_STOCK_CSV', '../ML/data/Stock.csv'),

    'item_master_csv' => env('MYVENTORY_ITEM_MASTER_CSV', '../ML/data/ItemMaster.csv'),
];
