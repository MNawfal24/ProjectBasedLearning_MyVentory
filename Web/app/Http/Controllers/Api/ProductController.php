<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\Api\StoreProductRequest;
use App\Http\Requests\Api\UpdateProductRequest;
use App\Http\Resources\Api\ProductResource;
use App\Models\Outlet;
use App\Models\Product;
use App\Models\Stock;
use App\Services\StockLedger;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;
use Illuminate\Support\Arr;
use Illuminate\Validation\ValidationException;

class ProductController extends Controller
{
    public function index(Request $request): AnonymousResourceCollection
    {
        $outletId = $request->integer('outlet_id') ?: $this->defaultOutletId();

        $query = Product::query()
            ->withSum('items as sold_quantity', 'quantity')
            ->with(['stocks' => fn ($query) => $query->where('outlet_id', $outletId)]);

        if ($search = $request->string('search')->trim()->toString()) {
            $query->where(function ($query) use ($search) {
                $query->where('name', 'like', "%{$search}%")
                    ->orWhere('sku', 'like', "%{$search}%");
            });
        }

        if ($category = $request->string('category')->trim()->toString()) {
            $query->where('category', $category);
        }

        if ($request->has('is_active')) {
            $query->where('is_active', $request->boolean('is_active'));
        }

        $perPage = min(max($request->integer('per_page', 50), 1), 100);

        return ProductResource::collection($query->orderBy('name')->paginate($perPage));
    }

    public function store(StoreProductRequest $request, StockLedger $ledger): JsonResponse
    {
        $data = $request->validated();
        $outlet = $this->resolveOutlet($data['outlet_id'] ?? null);

        $product = Product::create([
            'name' => $data['name'],
            'sku' => $data['sku'] ?? null,
            'category' => $data['category'] ?? null,
            'unit' => $data['unit'],
            'sell_price' => $data['sell_price'],
            'buy_price' => $data['buy_price'] ?? 0,
            'is_active' => $data['is_active'] ?? true,
        ]);

        $this->applyStock($outlet, $product, $data, $ledger);

        return (new ProductResource($this->loadProduct($product, $outlet->id)))
            ->response()
            ->setStatusCode(201);
    }

    public function show(Request $request, Product $product): ProductResource
    {
        $outletId = $request->integer('outlet_id') ?: $this->defaultOutletId();

        return new ProductResource($this->loadProduct($product, $outletId));
    }

    public function update(UpdateProductRequest $request, Product $product, StockLedger $ledger): ProductResource
    {
        $data = $request->validated();
        $outlet = $this->resolveOutlet($data['outlet_id'] ?? null);

        $product->fill(Arr::only($data, [
            'name',
            'sku',
            'category',
            'unit',
            'sell_price',
            'buy_price',
            'is_active',
        ]))->save();

        $this->applyStock($outlet, $product, $data, $ledger);

        return new ProductResource($this->loadProduct($product, $outlet->id));
    }

    public function destroy(Product $product): JsonResponse
    {
        $product->delete();

        return response()->json(['message' => 'Produk dihapus.']);
    }

    private function applyStock(Outlet $outlet, Product $product, array $data, StockLedger $ledger): void
    {
        if (array_key_exists('stock', $data) && $data['stock'] !== null) {
            $current = (float) Stock::query()
                ->where('outlet_id', $outlet->id)
                ->where('product_id', $product->id)
                ->value('quantity');

            $target = (float) $data['stock'];
            $delta = $target - $current;

            if (abs($delta) >= 0.005) {
                $ledger->record(
                    $outlet,
                    $product,
                    'adjustment',
                    $delta,
                    'product-form',
                    'Penyesuaian stok dari form produk.',
                );
            } else {
                Stock::firstOrCreate(
                    ['outlet_id' => $outlet->id, 'product_id' => $product->id],
                    ['quantity' => $current, 'min_quantity' => 0],
                );
            }
        } else {
            Stock::firstOrCreate(
                ['outlet_id' => $outlet->id, 'product_id' => $product->id],
                ['quantity' => 0, 'min_quantity' => 0],
            );
        }

        if (array_key_exists('min_stock', $data) && $data['min_stock'] !== null) {
            $ledger->setMinimum($outlet, $product, (float) $data['min_stock']);
        }
    }

    private function loadProduct(Product $product, ?int $outletId): Product
    {
        $product->loadSum('items as sold_quantity', 'quantity');
        $product->load(['stocks' => fn ($query) => $query->where('outlet_id', $outletId)]);

        return $product;
    }

    private function resolveOutlet(?int $outletId): Outlet
    {
        if ($outletId) {
            return Outlet::query()->findOrFail($outletId);
        }

        $outlet = Outlet::query()->orderBy('id')->first();

        if (! $outlet) {
            throw ValidationException::withMessages([
                'outlet_id' => ['Belum ada outlet. Jalankan seeder terlebih dahulu.'],
            ]);
        }

        return $outlet;
    }

    private function defaultOutletId(): ?int
    {
        return Outlet::query()->orderBy('id')->value('id');
    }
}
