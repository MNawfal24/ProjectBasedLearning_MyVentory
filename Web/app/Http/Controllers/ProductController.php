<?php

namespace App\Http\Controllers;

use App\Models\Product;
use Illuminate\Http\Request;
use Inertia\Inertia;
use Inertia\Response;

class ProductController extends Controller
{
    public function index(Request $request): Response
    {
        $query = Product::query()->withSum('items as sold_quantity', 'quantity');

        if ($search = $request->string('search')->trim()->toString()) {
            $query->where('name', 'like', "%{$search}%");
        }

        return Inertia::render('Products/Index', [
            'products' => $query->orderBy('name')->get()->map(fn (Product $product) => [
                'id' => $product->id,
                'sku' => $product->sku,
                'name' => $product->name,
                'category' => $product->category,
                'unit' => $product->unit,
                'sell_price' => (float) $product->sell_price,
                'is_active' => $product->is_active,
                'sold_quantity' => (int) ($product->sold_quantity ?? 0),
            ]),
            'filters' => ['search' => $request->string('search')->toString()],
        ]);
    }

    public function store(Request $request)
    {
        Product::create($this->validated($request));

        return back()->with('success', 'Produk ditambahkan.');
    }

    public function update(Request $request, Product $product)
    {
        $product->update($this->validated($request, $product));

        return back()->with('success', 'Produk diperbarui.');
    }

    private function validated(Request $request, ?Product $product = null): array
    {
        $data = $request->validate([
            'name' => ['required', 'string', 'max:255', 'unique:products,name'.($product ? ",{$product->id}" : '')],
            'sku' => ['nullable', 'string', 'max:32', 'unique:products,sku'.($product ? ",{$product->id}" : '')],
            'category' => ['nullable', 'string', 'max:48'],
            'unit' => ['required', 'string', 'max:16'],
            'sell_price' => ['required', 'numeric', 'min:0', 'max:10000000'],
            'is_active' => ['boolean'],
        ]);

        // An empty form field arrives as "", which would collide with the unique
        // index once two products leave SKU blank.
        $data['sku'] = filled($data['sku'] ?? null) ? $data['sku'] : null;
        $data['category'] = filled($data['category'] ?? null) ? $data['category'] : null;
        $data['is_active'] = (bool) ($data['is_active'] ?? true);

        return $data;
    }
}
