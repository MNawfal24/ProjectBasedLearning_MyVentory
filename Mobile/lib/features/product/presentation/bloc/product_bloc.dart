import 'package:flutter/foundation.dart';

import '../../domain/entities/product.dart';
import '../../domain/usecases/add_product.dart';
import '../../domain/usecases/get_product_by_id.dart';
import '../../domain/usecases/get_products.dart';
import '../../domain/usecases/get_low_stock_products.dart';
import '../../domain/usecases/get_product_stats.dart';
import '../../domain/usecases/update_product.dart';
import '../../domain/usecases/delete_product.dart';

class ProductBloc extends ChangeNotifier {
  final GetProducts getProducts;
  final GetProductById getProductById;
  final GetLowStockProducts getLowStockProducts;
  final GetProductStats getProductStats;
  final AddProduct addProduct;
  final UpdateProduct updateProduct;
  final DeleteProduct deleteProduct;

  ProductBloc({
    required this.getProducts,
    required this.getProductById,
    required this.getLowStockProducts,
    required this.getProductStats,
    required this.addProduct,
    required this.updateProduct,
    required this.deleteProduct,
  });

  List<Product> _products = [];
  List<Product> get products => _products;
  List<Product> get lowStockProducts => getLowStockProducts();
  Map<String, int> get stats => getProductStats();

  bool _loading = false;
  bool get loading => _loading;
  String? _error;
  String? get error => _error;

  Future<void> loadProducts({String? outletId}) async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      _products = await getProducts(outletId: outletId);
    } catch (e) {
      _error = e.toString();
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<Product?> getProduct(String id) async {
    try {
      return await getProductById(id);
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return null;
    }
  }

  Future<void> addProductAction(Product product) async {
    try {
      await addProduct(product);
      await loadProducts();
    } catch (e) {
      _error = e.toString();
    } finally {
      notifyListeners();
    }
  }

  Future<void> updateProductAction(Product product) async {
    try {
      await updateProduct(product);
      await loadProducts();
    } catch (e) {
      _error = e.toString();
    } finally {
      notifyListeners();
    }
  }

  Future<void> deleteProductAction(String id) async {
    try {
      await deleteProduct(id);
      _products.removeWhere((p) => p.id == id);
    } catch (e) {
      _error = e.toString();
    } finally {
      notifyListeners();
    }
  }
}
