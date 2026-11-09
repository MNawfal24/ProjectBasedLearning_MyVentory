<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\Api\LoginRequest;
use App\Http\Resources\Api\UserResource;
use App\Models\User;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\ValidationException;

class AuthController extends Controller
{
    public function login(LoginRequest $request): JsonResponse
    {
        $user = User::query()->where('email', $request->string('email')->toString())->first();

        if (! $user || ! Hash::check($request->string('password')->toString(), $user->password)) {
            throw ValidationException::withMessages([
                'email' => ['Email atau password salah.'],
            ]);
        }

        // The dashboard owns admin sessions; the mobile app is for staff accounts.
        if ($request->string('client')->toString() === 'mobile' && $user->isAdmin()) {
            return response()->json([
                'message' => 'Akun admin hanya dapat masuk melalui dashboard web.',
            ], 403);
        }

        $token = $user->createToken(
            $request->string('device_name', 'mobile')->toString(),
            $this->abilitiesFor($user),
        )->plainTextToken;

        return response()->json([
            'token' => $token,
            'token_type' => 'Bearer',
            'user' => new UserResource($user),
        ]);
    }

    public function me(Request $request): UserResource
    {
        return new UserResource($request->user());
    }

    public function logout(Request $request): JsonResponse
    {
        $request->user()->currentAccessToken()?->delete();

        return response()->json(['message' => 'Logout berhasil.']);
    }

    /**
     * @return list<string>
     */
    private function abilitiesFor(User $user): array
    {
        return $user->isAdmin() ? ['read', 'write'] : ['read'];
    }
}
