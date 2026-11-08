<?php

namespace App\Http\Requests\Api;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

class StoreProductRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'name' => ['required', 'string', 'max:255', 'unique:products,name'],
            'sku' => ['nullable', 'string', 'max:32', 'unique:products,sku'],
            'category' => ['nullable', 'string', 'max:48'],
            'unit' => ['required', 'string', 'max:16'],
            'sell_price' => ['required', 'numeric', 'min:0', 'max:10000000'],
            'buy_price' => ['nullable', 'numeric', 'min:0', 'max:10000000'],
            'is_active' => ['sometimes', 'boolean'],
            'outlet_id' => ['nullable', 'integer', Rule::exists('outlets', 'id')],
            'stock' => ['nullable', 'numeric', 'min:0', 'max:1000000'],
            'min_stock' => ['nullable', 'numeric', 'min:0', 'max:1000000'],
        ];
    }

    protected function prepareForValidation(): void
    {
        $this->merge([
            'sku' => filled($this->input('sku')) ? $this->input('sku') : null,
            'category' => filled($this->input('category')) ? $this->input('category') : null,
        ]);
    }
}
