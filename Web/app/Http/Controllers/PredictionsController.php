<?php

namespace App\Http\Controllers;

use App\Models\Product;
use App\Services\MlClient;
use Illuminate\Http\Request;
use Inertia\Inertia;
use Inertia\Response;
use RuntimeException;

class PredictionsController extends Controller
{
    public function index(Request $request, MlClient $ml): Response
    {
        $products = Product::query()
            ->where('is_active', true)
            ->orderBy('name')
            ->pluck('name')
            ->all();

        $product = (string) $request->query('product', '');
        if (! in_array($product, $products, true)) {
            $product = $products[0] ?? null;
        }

        $horizon = max(1, min(14, (int) $request->query('horizon_days', 7)));

        $demand = $product === null
            ? ['error' => 'Belum ada produk aktif untuk diprediksi.']
            : $this->predict($ml, '/demand-forecast', [
                'outlet' => null,
                'product' => $product,
                'horizon_days' => $horizon,
            ]);

        return Inertia::render('Predictions/Index', [
            'products' => $products,
            'demand_filters' => [
                'product' => $product,
                'horizon_days' => $horizon,
            ],
            'demand' => $demand,
            'segmentation' => $this->predict($ml, '/segmentation', ['products' => $products]),
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
