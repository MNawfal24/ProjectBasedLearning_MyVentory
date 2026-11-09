/// Konfigurasi jaringan API.
///
/// Base URL dapat di-override saat build dengan:
///   flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000/api/v1
///
/// Secara default menunjuk ke Laravel development server yang dijalankan
/// secara lokal (`php artisan serve --port=8000`) dan diakses dari emulator
/// Android melalui alamat router emulasi `10.0.2.2`.
class ApiConfig {
  static String get baseUrl =>
      String.fromEnvironment('API_BASE_URL',
          defaultValue: 'http://10.0.2.2:8000/api/v1');

  static const Duration connectTimeout = Duration(seconds: 15);
  static const Duration receiveTimeout = Duration(seconds: 15);
}
