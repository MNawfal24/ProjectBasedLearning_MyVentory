<?php

namespace App\Http\Controllers;

use App\Models\Product;
use App\Services\MlClient;
use Inertia\Inertia;
use Inertia\Response;
use RuntimeException;

class PredictionsController extends Controller
{
    public function index(MlClient $ml): Response
    {
        return Inertia::render('Predictions/Index', [
            'segmentation' => $this->predict($ml, '/segmentation', ['products' => Product::query()->where('is_active', true)->pluck('name')->all()]),
        ]);
    }

    private function predict(MlClient $ml, string $endpoint, array $payload): ?array
    {
        try {
            $response = $ml->post($endpoint, $payload);
            return $response->successful() ? $response->json() : ['error' => $response->json('error.message') ?? 'Prediksi tidak tersedia.'];
        } catch (RuntimeException) {
            return ['error' => 'Layanan prediksi sedang tidak tersedia.'];
        }
    }
}
