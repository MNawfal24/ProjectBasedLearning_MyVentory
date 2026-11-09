<?php

namespace App\Http\Controllers\Web;

use App\Http\Controllers\Controller;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;

class LandingController extends Controller
{
    public function index(Request $request): RedirectResponse
    {
        return to_route($request->user() ? 'dashboard' : 'login');
    }
}
