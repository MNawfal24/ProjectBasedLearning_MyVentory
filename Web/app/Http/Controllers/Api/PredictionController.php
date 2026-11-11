<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Outlet;
use App\Models\Product;
use App\Models\Stock;
use App\Services\MlClient;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;
use RuntimeException;

class PredictionController extends Controller
{
    public function salesForecast(Request $request, MlClient $ml): JsonResponse
    {
        $data = $request->validate([
            'outlet_id' => ['required', 'integer', Rule::exists('outlets', 'id')],
            'horizon_days' => ['nullable', 'integer', 'between:1,14'],
        ]);

        $outlet = Outlet::query()->findOrFail($data['outlet_id']);

        return $this->forward($ml, '/sales-forecast', [
            'outlet' => $outlet->code,
            'horizon_days' => (int) ($data['horizon_days'] ?? 7),
        ]);
    }

    public function demandForecast(Request $request, MlClient $ml): JsonResponse
    {
        $data = $request->validate([
            'outlet_id' => ['required', 'integer', Rule::exists('outlets', 'id')],
            'product_id' => ['required', 'integer', Rule::exists('products', 'id')],
            'horizon_days' => ['nullable', 'integer', 'between:1,14'],
        ]);

        $outlet = Outlet::query()->findOrFail($data['outlet_id']);
        $product = Product::query()->findOrFail($data['product_id']);

        return $this->forward($ml, '/demand-forecast', [
            'outlet' => $outlet->code,
            'product' => $product->name,
            'horizon_days' => (int) ($data['horizon_days'] ?? 7),
        ]);
    }

    public function stockPrediction(Request $request, MlClient $ml): JsonResponse
    {
        $data = $request->validate([
            'outlet_id' => ['required', 'integer', Rule::exists('outlets', 'id')],
            'product_id' => ['required', 'integer', Rule::exists('products', 'id')],
            'horizon_days' => ['nullable', 'integer', 'between:1,14'],
        ]);

        $outlet = Outlet::query()->findOrFail($data['outlet_id']);
        $product = Product::query()->findOrFail($data['product_id']);

        $available = (float) (Stock::query()
            ->where('outlet_id', $outlet->id)
            ->where('product_id', $product->id)
            ->value('quantity') ?? 0);

        return $this->forward($ml, '/stock-prediction', [
            'outlet' => $outlet->code,
            'product' => $product->sku,
            'horizon_days' => (int) ($data['horizon_days'] ?? 7),
            'available_stock' => $available,
        ]);
    }

    private function forward(MlClient $ml, string $endpoint, array $payload): JsonResponse
    {
        try {
            $response = $ml->post($endpoint, $payload);
        } catch (RuntimeException $e) {
            return response()->json(['message' => $e->getMessage()], 503);
        }

        if ($response->failed()) {
            return response()->json([
                'message' => $response->json('error.message') ?? 'Layanan prediksi menolak permintaan.',
                'details' => $response->json('error.details'),
            ], $response->status() === 422 ? 422 : 503);
        }

        return response()->json(['data' => $response->json()]);
    }
}
