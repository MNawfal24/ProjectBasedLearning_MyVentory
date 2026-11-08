import 'package:flutter/foundation.dart';

import '../features/product/domain/entities/product.dart';
import '../injection_container.dart';

class InventoryStore extends ChangeNotifier {
  List<Product> get products => sl.getProducts();

  List<Product> get lowStockProducts => sl.getLowStockProducts();

  int get totalProducts => sl.productRepository.getTotalProducts();

  int get totalLowStock => sl.productRepository.getTotalLowStock();

  int get totalStock => sl.productRepository.getTotalStock();

  Product getProductById(String id) {
    return sl.getProductById(id);
  }

  void addProduct(Product product) {
    sl.addProduct(product);
    notifyListeners();
  }

  void updateProduct(Product updatedProduct) {
    sl.updateProduct(updatedProduct);
    notifyListeners();
  }

  int predictedDemand(Product product) {
    return sl.getPredictedDemand(product);
  }

  int recommendedRestock(Product product) {
    return sl.getRecommendedRestock(product);
  }
}
