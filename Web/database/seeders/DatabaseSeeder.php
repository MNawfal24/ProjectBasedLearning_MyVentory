<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        $this->call(TransactionImportSeeder::class);
        $this->call(StockImportSeeder::class);

        User::query()->updateOrCreate(
            ['email' => env('MYVENTORY_ADMIN_EMAIL', 'admin@myventory.com')],
            [
                'name' => env('MYVENTORY_ADMIN_NAME', 'Admin MyVentory'),
                'password' => Hash::make(env('MYVENTORY_ADMIN_PASSWORD', 'admin123')),
                'role' => User::ROLE_ADMIN,
            ],
        );
    }
}
