import 'package:dio/dio.dart';

/// Akses data mentah ke endpoint autentikasi Laravel (Sanctum).
class AuthRemoteDataSource {
  final Dio dio;

  AuthRemoteDataSource(this.dio);

  /// Masuk dan ambil token + data pengguna.
  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
    String? deviceName,
  }) async {
    final response = await dio.post('/auth/login', data: {
      'email': email,
      'password': password,
      'device_name': deviceName ?? 'mobile',
    });
    return response.data as Map<String, dynamic>;
  }

  /// Keluar dan hapus token di server.
  Future<void> logout() async {
    await dio.post('/auth/logout');
  }

  /// Ambil profil pengguna yang sedang masuk.
  Future<Map<String, dynamic>> me() async {
    final response = await dio.get('/auth/me');
    return response.data as Map<String, dynamic>;
  }
}
