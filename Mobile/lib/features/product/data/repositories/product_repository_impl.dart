import 'package:myventory/features/product/data/product_remote_datasource.dart';
import 'package:myventory/features/product/domain/entities/product.dart';
import 'package:myventory/features/product/domain/repositories/product_repository.dart';

/// Implementasi repositori produk yang didukung oleh API Laravel (Sanctum).
class ProductRepositoryImpl implements ProductRepository {
  final ProductRemoteDataSource _remote;

  ProductRepositoryImpl(this._remote);

  final List<Product> _products = [];

  @override
  List<Product> get products => List.unmodifiable(_products);

  @override
  List<Product> getLowStockProducts() =>
      _products.where((product) => product.isLowStock).toList();

  @override
  int getTotalProducts() => _products.length;

  @override
  int getTotalLowStock() => getLowStockProducts().length;

  @override
  int getTotalStock() =>
      _products.fold(0, (sum, product) => sum + product.stock);

  @override
  Future<void> loadProducts({String? outletId}) async {
    _products
      ..clear()
      ..addAll(await _remote.getProducts(outletId: outletId));
  }

  @override
  Future<Product> getProductById(String id, {String? outletId}) async {
    final cached = _products.firstWhereOrNull((p) => p.id == id);
    if (cached != null) return cached;
    return await _remote.getProductById(id, outletId: outletId);
  }

  @override
  Future<Product> addProduct(Product product) async {
    final created = await _remote.addProduct(product);
    _products.add(created);
    return created;
  }

  @override
  Future<Product> updateProduct(Product product) async {
    final updated = await _remote.updateProduct(product);
    final index = _products.indexWhere((p) => p.id == product.id);
    if (index != -1) {
      _products[index] = updated;
    } else {
      _products.add(updated);
    }
    return updated;
  }

  @override
  Future<void> deleteProduct(String id) async {
    await _remote.deleteProduct(id);
    _products.removeWhere((p) => p.id == id);
  }

  @override
  Future<void> adjustStock({
    required String outletId,
    required String productId,
    required String type,
    required double quantity,
    String? note,
  }) async {
    await _remote.recordStockMovement(
      outletId: outletId,
      productId: productId,
      type: type,
      quantity: quantity,
      note: note,
    );
    await loadProducts(outletId: outletId);
  }

  @override
  Future<void> setMinStock(String stockId, double minQuantity) async {
    await _remote.setMinStock(stockId, minQuantity);
  }
}

extension _FirstWhereOrNull<E> on Iterable<E> {
  E? firstWhereOrNull(bool Function(E) test) {
    for (final element in this) {
      if (test(element)) return element;
    }
    return null;
  }
}
