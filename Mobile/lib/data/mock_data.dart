import 'package:flutter/foundation.dart';

import '../models/product_model.dart';

class InventoryStore extends ChangeNotifier {
  final List<Product> products = [
    Product(
      id: 'P001',
      name: 'Kopi Arabica',
      category: 'Coffee',
      stock: 25,
      minStock: 10,
      unit: 'Kg',
      buyPrice: 85000,
      sellPrice: 125000,
    ),
    Product(
      id: 'P002',
      name: 'Susu Full Cream',
      category: 'Dairy',
      stock: 8,
      minStock: 10,
      unit: 'Liter',
      buyPrice: 18000,
      sellPrice: 25000,
    ),
    Product(
      id: 'P003',
      name: 'Gula Aren',
      category: 'Sweetener',
      stock: 15,
      minStock: 8,
      unit: 'Kg',
      buyPrice: 45000,
      sellPrice: 65000,
    ),
    Product(
      id: 'P004',
      name: 'Cokelat Bubuk',
      category: 'Ingredient',
      stock: 6,
      minStock: 8,
      unit: 'Kg',
      buyPrice: 55000,
      sellPrice: 80000,
    ),
    Product(
      id: 'P005',
      name: 'Matcha Powder',
      category: 'Ingredient',
      stock: 12,
      minStock: 5,
      unit: 'Kg',
      buyPrice: 110000,
      sellPrice: 150000,
    ),
  ];

  List<Product> get lowStockProducts {
    return products.where((product) => product.isLowStock).toList();
  }

  int get totalProducts => products.length;

  int get totalLowStock => lowStockProducts.length;

  int get totalStock {
    return products.fold(0, (sum, product) => sum + product.stock);
  }

  Product getProductById(String id) {
    return products.firstWhere((product) => product.id == id);
  }

  void addProduct(Product product) {
    products.add(product);
    notifyListeners();
  }

  void updateProduct(Product updatedProduct) {
    final index = products.indexWhere(
      (product) => product.id == updatedProduct.id,
    );

    if (index != -1) {
      products[index] = updatedProduct;
      notifyListeners();
    }
  }

  int predictedDemand(Product product) {
    switch (product.id) {
      case 'P001':
        return 30;
      case 'P002':
        return 18;
      case 'P003':
        return 14;
      case 'P004':
        return 12;
      case 'P005':
        return 9;
      default:
        return 10;
    }
  }

  int recommendedRestock(Product product) {
    final demand = predictedDemand(product);

    const safetyStock = 5;

    final recommendation =
        demand + safetyStock - product.stock;

    return recommendation > 0 ? recommendation : 0;
  }
}
