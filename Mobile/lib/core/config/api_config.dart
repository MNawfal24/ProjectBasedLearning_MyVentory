/// Override saat build: --dart-define=API_BASE_URL=http://192.168.1.10:8080/api/v1
/// Port 8080 adalah Laravel (web + API); 8000 hanya FastAPI internal.
class ApiConfig {
  static String get baseUrl =>
      String.fromEnvironment('API_BASE_URL',
          defaultValue: 'http://10.0.2.2:8080/api/v1');

  static const Duration connectTimeout = Duration(seconds: 15);
  static const Duration receiveTimeout = Duration(seconds: 15);
}
