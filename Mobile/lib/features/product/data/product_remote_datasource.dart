import 'package:dio/dio.dart';

import 'package:myventory/features/product/domain/entities/product.dart';

/// Akses data mentah ke endpoint produk, stok, dan ringkasan Laravel API.
class ProductRemoteDataSource {
  final Dio dio;

  ProductRemoteDataSource(this.dio);

  /// Daftar produk beserta saldo stok di outlet tertentu.
  Future<List<Product>> getProducts({String? outletId}) async {
    final query = <String, dynamic>{};
    if (outletId != null && outletId.isNotEmpty) {
      query['outlet_id'] = outletId;
    }
    final response = await dio.get('/products', queryParameters: query);
    final data = response.data as Map<String, dynamic>;
    final list = (data['data'] as List? ?? <dynamic>[]);
    return list
        .map((e) => _productFromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Detail satu produk.
  Future<Product> getProductById(String id, {String? outletId}) async {
    final query = <String, dynamic>{};
    if (outletId != null && outletId.isNotEmpty) {
      query['outlet_id'] = outletId;
    }
    final response = await dio.get('/products/$id', queryParameters: query);
    return _productFromJson(response.data['data'] as Map<String, dynamic>);
  }

  /// Tambah produk (termasuk saldo stok awal jika disediakan).
  Future<Product> addProduct(Product product) async {
    final response = await dio.post('/products', data: _productToRequest(product));
    return _productFromJson(response.data['data'] as Map<String, dynamic>);
  }

  /// Perbarui produk (termasuk penyesuaian stok via StockLedger di server).
  Future<Product> updateProduct(Product product) async {
    final response = await dio.patch('/products/${product.id}', data: _productToRequest(product));
    return _productFromJson(response.data['data'] as Map<String, dynamic>);
  }

  /// Hapus produk (soft delete di server).
  Future<void> deleteProduct(String id) async {
    await dio.delete('/products/$id');
  }

  /// Catat pergerakan stok melalui StockLedger di server.
  Future<void> recordStockMovement({
    required String outletId,
    required String productId,
    required String type,
    required double quantity,
    String? note,
  }) async {
    await dio.post('/stocks/movements', data: {
      'outlet_id': outletId,
      'product_id': productId,
      'type': type,
      'quantity': quantity,
      'note': note,
    });
  }

  /// Perbarui jumlah minimum stok.
  Future<void> setMinStock(String stockId, double minQuantity) async {
    await dio.patch('/stocks/$stockId', data: {'min_quantity': minQuantity});
  }

  /// Daftar outlet.
  Future<List<Map<String, dynamic>>> getOutlets() async {
    final response = await dio.get('/outlets');
    return (response.data['data'] as List).cast<Map<String, dynamic>>();
  }

  /// Ringkasan dashboard.
  Future<Map<String, dynamic>> getDashboardSummary({int days = 30, String? outletId}) async {
    final query = <String, dynamic>{'days': days};
    if (outletId != null && outletId.isNotEmpty) {
      query['outlet_id'] = outletId;
    }
    final response = await dio.get('/dashboard/summary', queryParameters: query);
    return response.data['stats'] as Map<String, dynamic>;
  }

  Product _productFromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id'].toString(),
      name: json['name'] ?? '',
      category: json['category'] ?? '',
      unit: (json['unit'] ?? 'pcs').toString(),
      buyPrice: _toDouble(json['buy_price']),
      sellPrice: _toDouble(json['sell_price']),
      stock: _toInt(json['stock']),
      minStock: _toInt(json['min_stock']),
      sku: json['sku'],
      isActive: json['is_active'] == true,
      stockId: json['stock_id']?.toString(),
      outletId: json['outlet_id']?.toString(),
    );
  }

  Map<String, dynamic> _productToRequest(Product product) {
    return {
      'name': product.name,
      'sku': product.sku,
      'category': product.category,
      'unit': product.unit,
      'sell_price': product.sellPrice,
      'buy_price': product.buyPrice,
      'is_active': product.isActive,
      'outlet_id': product.outletId,
      'stock': product.stock,
      'min_stock': product.minStock,
    };
  }

  double _toDouble(dynamic v) {
    if (v == null) return 0.0;
    if (v is num) return v.toDouble();
    return double.tryParse(v.toString()) ?? 0.0;
  }

  int _toInt(dynamic v) {
    if (v == null) return 0;
    if (v is num) return v.round();
    return int.tryParse(v.toString()) ?? 0;
  }
}
