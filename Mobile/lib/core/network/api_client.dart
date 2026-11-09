import 'package:dio/dio.dart';

import 'package:myventory/core/config/api_config.dart';
import 'package:myventory/core/models/api_exception.dart';
import 'package:myventory/core/storage/token_storage.dart';

/// Klien HTTP berbasis Dio dengan:
/// - base URL terpusat ([ApiConfig]);
/// - pemasangan otomatis header `Authorization: Bearer <token>`;
/// - penanganan respons 401 (hapus token dan pemberitahuan auth);
/// - pemetaan kesalahan ke [ApiException].
class ApiClient {
  Dio? _dio;

  /// Dipanggil ketika respons 401 diterima agar UI dapat mengarahkan ke login.
  static void Function(bool authenticated)? onAuthStateChanged;

  Dio get dio {
    _dio ??= _buildDio();
    return _dio!;
  }

  Dio _buildDio() {
    final dio = Dio(
      BaseOptions(
        baseUrl: ApiConfig.baseUrl,
        connectTimeout: ApiConfig.connectTimeout,
        receiveTimeout: ApiConfig.receiveTimeout,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      ),
    );

    dio.interceptors.addAll([
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await TokenStorage.read();
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          return handler.next(options);
        },
      ),
      InterceptorsWrapper(
        onError: (DioException error, handler) async {
          final statusCode = error.response?.statusCode;
          if (statusCode == 401) {
            await TokenStorage.clear();
            onAuthStateChanged?.call(false);
          }
          return handler.next(error);
        },
      ),
    ]);

    return dio;
  }

  /// Ubah [DioException] atau kesalahan lain menjadi [ApiException].
  static ApiException errorFrom(Object error) => ApiException.fromDio(error);
}
