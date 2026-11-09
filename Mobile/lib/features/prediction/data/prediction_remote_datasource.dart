import 'package:dio/dio.dart';

/// Prediksi ML melalui proxy Laravel. Mobile tidak pernah memanggil FastAPI
/// langsung: layanan ML tidak punya autentikasi.
class PredictionRemoteDataSource {
  final Dio dio;

  PredictionRemoteDataSource(this.dio);

  Future<Map<String, dynamic>> demandForecast({
    required String outletId,
    required String productId,
    int horizonDays = 7,
  }) async {
    final response = await dio.get('/predictions/demand-forecast', queryParameters: {
      'outlet_id': outletId,
      'product_id': productId,
      'horizon_days': horizonDays,
    });
    return response.data['data'] as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> stockPrediction({
    required String outletId,
    required String productId,
    int horizonDays = 7,
  }) async {
    final response = await dio.get('/predictions/stock', queryParameters: {
      'outlet_id': outletId,
      'product_id': productId,
      'horizon_days': horizonDays,
    });
    return response.data['data'] as Map<String, dynamic>;
  }
}
