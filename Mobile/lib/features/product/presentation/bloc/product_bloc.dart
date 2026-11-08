import 'package:flutter/foundation.dart';

import '../../domain/entities/product.dart';
import '../../domain/usecases/add_product.dart';
import '../../domain/usecases/get_product_by_id.dart';
import '../../domain/usecases/get_products.dart';
import '../../domain/usecases/update_product.dart';
import '../../domain/usecases/get_low_stock_products.dart';
import '../../domain/usecases/get_product_stats.dart';

class ProductBloc extends ChangeNotifier {
  final GetProducts getProducts;
  final GetProductById getProductById;
  final GetLowStockProducts getLowStockProducts;
  final GetProductStats getProductStats;
  final AddProduct addProduct;
  final UpdateProduct updateProduct;

  ProductBloc({
    required this.getProducts,
    required this.getProductById,
    required this.getLowStockProducts,
    required this.getProductStats,
    required this.addProduct,
    required this.updateProduct,
  });

  List<Product> get products => getProducts();
  Product getProduct(String id) => getProductById(id);
  List<Product> get lowStockProducts => getLowStockProducts();
  Map<String, int> get stats => getProductStats();

  void addProductAction(Product product) {
    addProduct(product);
    notifyListeners();
  }

  void updateProductAction(Product product) {
    updateProduct(product);
    notifyListeners();
  }
}
