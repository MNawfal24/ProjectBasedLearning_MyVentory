<?php

namespace App\Http\Requests\Api;

use App\Models\Product;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

class UpdateProductRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        $product = $this->route('product');
        $productId = $product instanceof Product ? $product->id : $product;

        return [
            'name' => ['sometimes', 'required', 'string', 'max:255', Rule::unique('products', 'name')->ignore($productId)],
            'sku' => ['sometimes', 'nullable', 'string', 'max:32', Rule::unique('products', 'sku')->ignore($productId)],
            'category' => ['sometimes', 'nullable', 'string', 'max:48'],
            'unit' => ['sometimes', 'required', 'string', 'max:16'],
            'sell_price' => ['sometimes', 'numeric', 'min:0', 'max:10000000'],
            'buy_price' => ['sometimes', 'nullable', 'numeric', 'min:0', 'max:10000000'],
            'supplier_name' => ['sometimes', 'nullable', 'string', 'max:120'],
            'supplier_phone' => ['sometimes', 'nullable', 'string', 'max:20', 'regex:/^[0-9+\-\s()]{8,20}$/'],
            'is_active' => ['sometimes', 'boolean'],
            'outlet_id' => ['sometimes', 'nullable', 'integer', Rule::exists('outlets', 'id')],
            'stock' => ['sometimes', 'nullable', 'numeric', 'min:0', 'max:1000000'],
            'min_stock' => ['sometimes', 'nullable', 'numeric', 'min:0', 'max:1000000'],
        ];
    }

    protected function prepareForValidation(): void
    {
        if ($this->has('sku')) {
            $this->merge(['sku' => filled($this->input('sku')) ? $this->input('sku') : null]);
        }
        foreach (['supplier_name', 'supplier_phone'] as $field) {
            if ($this->has($field)) {
                $this->merge([$field => filled($this->input($field)) ? trim($this->input($field)) : null]);
            }
        }
        if ($this->has('category')) {
            $this->merge(['category' => filled($this->input('category')) ? $this->input('category') : null]);
        }
    }
}