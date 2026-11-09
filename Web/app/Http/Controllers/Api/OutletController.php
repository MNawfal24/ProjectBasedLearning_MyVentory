<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Resources\Api\OutletResource;
use App\Models\Outlet;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;

class OutletController extends Controller
{
    public function index(): AnonymousResourceCollection
    {
        return OutletResource::collection(Outlet::query()->orderBy('code')->get());
    }

    public function show(Outlet $outlet): OutletResource
    {
        return new OutletResource($outlet);
    }
}
