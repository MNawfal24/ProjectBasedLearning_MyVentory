/// Kesalahan respons dari API Laravel.
import 'package:dio/dio.dart';

class ApiException implements Exception {
  final int? statusCode;
  final String message;
  final Map<String, dynamic>? errors;

  ApiException({
    required this.message,
    this.statusCode,
    this.errors,
  });

  factory ApiException.fromDio(Object error) {
    if (error is DioException) {
      final response = error.response;
      final statusCode = response?.statusCode;
      final data = response?.data;

      String message;
      Map<String, dynamic>? errors;

      if (data is Map) {
        message = (data['message'] ?? data['error'] ?? 'Terjadi kesalahan').toString();
        errors = data['errors'] is Map ? Map<String, dynamic>.from(data['errors']) : null;
      } else {
        message = error.message ?? 'Terjadi kesalahan jaringan.';
        errors = null;
      }

      if (statusCode == 401) {
        message = 'Sesi habis atau tidak valid. Silakan masuk lagi.';
      } else if (statusCode == 403) {
        message = data is Map && data['message'] != null
            ? data['message'].toString()
            : 'Anda tidak diizinkan mengakses sumber daya ini.';
      } else if (statusCode == 422) {
        message = message.isNotEmpty ? message : 'Data yang dikirim tidak valid.';
      } else if (statusCode == null) {
        message = 'Tidak dapat terhubung ke server. Periksa koneksi dan base URL.';
      }

      return ApiException(
        message: message,
        statusCode: statusCode,
        errors: errors,
      );
    }

    return ApiException(message: error.toString());
  }

  @override
  String toString() => 'ApiException$statusCode: $message';
}
