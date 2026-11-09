import 'package:flutter/foundation.dart';

import 'package:myventory/core/network/api_client.dart';
import 'package:myventory/features/product/domain/entities/product.dart';
import 'package:myventory/injection_container.dart';

/// Sumber kebenaran tunggal untuk data produk yang disimpan di PostgreSQL
/// melalui Laravel REST API (tidak lagi data tiruan).
class InventoryStore extends ChangeNotifier {
  final List<Product> _products = [];
  final Map<String, int> _demandCache = {};
  final Map<String, List<Map<String, dynamic>>> _demandSeries = {};

  List<Product> get products => _products;
  List<Product> get lowStockProducts => sl.getLowStockProducts();
  int get totalProducts => sl.productRepository.getTotalProducts();
  int get totalLowStock => sl.productRepository.getTotalLowStock();
  int get totalStock => sl.productRepository.getTotalStock();

  bool _loading = false;
  bool get loading => _loading;

  String? _error;
  String? get error => _error;

  String? _message;
  String? get message => _message;

  /// Muat produk dan saldo stok terbaru dari API.
  Future<void> load({String? outletId}) async {
    _loading = true;
    _error = null;
    _message = null;
    notifyListeners();

    try {
      await sl.getProducts(outletId: outletId);
      _products
        ..clear()
        ..addAll(sl.productRepository.products);
    } catch (e) {
      _error = ApiClient.errorFrom(e).message;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Product? getProductById(String id) {
    for (final product in _products) {
      if (product.id == id) return product;
    }
    for (final product in sl.productRepository.products) {
      if (product.id == id) return product;
    }
    return null;
  }

  /// Tambah produk baru (dan saldo stok awal jika diisi).
  Future<void> addProduct(Product product) async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      await sl.addProduct(product);
      await load(outletId: product.outletId);
      _message = 'Produk ditambahkan.';
    } catch (e) {
      _error = ApiClient.errorFrom(e).message;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  /// Perbarui produk (informasi master produk tanpa menimpa saldo stok).
  Future<void> updateProduct(Product updatedProduct) async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      await sl.updateProduct(updatedProduct);
      await load(outletId: updatedProduct.outletId);
      _message = 'Produk diperbarui.';
    } catch (e) {
      _error = ApiClient.errorFrom(e).message;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  /// Hapus produk (soft delete di server).
  Future<void> deleteProduct(String id) async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      await sl.deleteProduct(id);
      _products.removeWhere((product) => product.id == id);
      _message = 'Produk dihapus.';
    } catch (e) {
      _error = ApiClient.errorFrom(e).message;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  /// Catat pergerakan stok (masuk/keluar/penyesuaian) via StockLedger di server.
  Future<void> adjustStock({
    required String outletId,
    required String productId,
    required String type,
    required double quantity,
    String? note,
  }) async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      await sl.productRepository.adjustStock(
        outletId: outletId,
        productId: productId,
        type: type,
        quantity: quantity,
        note: note,
      );
      await load(outletId: outletId);
      _message = 'Pergerakan stok tercatat.';
    } catch (e) {
      _error = ApiClient.errorFrom(e).message;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  /// Perbarui jumlah minimum stok.
  Future<void> setMinStock(String stockId, double minQuantity) async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      await sl.productRepository.setMinStock(stockId, minQuantity);
      await load();
      _message = 'Batas minimum stok diperbarui.';
    } catch (e) {
      _error = ApiClient.errorFrom(e).message;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  /// Ringkasan dashboard dari server.
  Future<Map<String, dynamic>> fetchDashboardSummary({
    int days = 30,
    String? outletId,
  }) async {
    return await sl.productRemoteDataSource.getDashboardSummary(
      days: days,
      outletId: outletId,
    );
  }

  /// Daftar outlet (untuk pemilihan outlet default).
  Future<List<Map<String, dynamic>>> fetchOutlets() async {
    return await sl.productRemoteDataSource.getOutlets();
  }

  int predictedDemand(Product product) => _demandCache[product.id] ?? 0;

  int recommendedRestock(Product product) {
    const safetyStock = 5;
    final quantity = predictedDemand(product) + safetyStock - product.stock;
    return quantity > 0 ? quantity : 0;
  }

  /// Rangkaian prediksi harian untuk grafik (kosong bila belum dimuat).
  List<Map<String, dynamic>> demandSeries(Product product) =>
      _demandSeries[product.id] ?? const [];

  /// Ambil prediksi permintaan dari model ML lewat Laravel, sekali per produk.
  Future<void> fetchDemand(Product product) async {
    final outletId = product.outletId;
    if (outletId == null || outletId.isEmpty) return;
    if (_demandCache.containsKey(product.id)) return;

    try {
      final data = await sl.predictionRemoteDataSource.demandForecast(
        outletId: outletId,
        productId: product.id,
      );

      final summary = data['summary'] as Map<String, dynamic>?;
      final total = summary?['total_predicted_qty'];
      _demandCache[product.id] = total is num ? total.round() : 0;

      final points = data['predictions'];
      if (points is List) {
        _demandSeries[product.id] = points
            .whereType<Map>()
            .map((point) => Map<String, dynamic>.from(point))
            .toList();
      }
    } catch (_) {
      // Dashboard web tetap sumber kebenaran; prediksi hanya pelengkap.
      _demandCache[product.id] = 0;
    } finally {
      notifyListeners();
    }
  }
}
