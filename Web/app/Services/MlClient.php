<?php

namespace App\Services;

use Illuminate\Http\Client\ConnectionException;
use Illuminate\Http\Client\Response;
use Illuminate\Support\Facades\Http;
use RuntimeException;

/**
 * Client for the FastAPI ML service. Laravel is the only caller: the ML image has
 * no auth or database, so it stays on the internal docker network.
 */
class MlClient
{
    public function post(string $endpoint, array $payload): Response
    {
        try {
            return Http::baseUrl(config('services.ml.base_url'))
                ->acceptJson()
                ->asJson()
                ->timeout((int) config('services.ml.timeout', 10))
                ->post(ltrim($endpoint, '/'), $payload);
        } catch (ConnectionException $e) {
            throw new RuntimeException('Layanan prediksi tidak dapat dihubungi.', 0, $e);
        }
    }
}
