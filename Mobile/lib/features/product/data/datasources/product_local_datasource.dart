import '../models/product_model.dart';

abstract class ProductLocalDataSource {
  List<ProductModel> getProducts();
  ProductModel getProductById(String id);
  void addProduct(ProductModel product);
  void updateProduct(ProductModel product);
}

class ProductLocalDataSourceImpl implements ProductLocalDataSource {
  final List<ProductModel> _products = [
    ProductModel(
      id: 'P001',
      name: 'Kopi Arabica',
      category: 'Coffee',
      stock: 25,
      minStock: 10,
      unit: 'Kg',
      buyPrice: 85000,
      sellPrice: 125000,
    ),
    ProductModel(
      id: 'P002',
      name: 'Susu Full Cream',
      category: 'Dairy',
      stock: 8,
      minStock: 10,
      unit: 'Liter',
      buyPrice: 18000,
      sellPrice: 25000,
    ),
    ProductModel(
      id: 'P003',
      name: 'Gula Aren',
      category: 'Sweetener',
      stock: 15,
      minStock: 8,
      unit: 'Kg',
      buyPrice: 45000,
      sellPrice: 65000,
    ),
    ProductModel(
      id: 'P004',
      name: 'Cokelat Bubuk',
      category: 'Ingredient',
      stock: 6,
      minStock: 8,
      unit: 'Kg',
      buyPrice: 55000,
      sellPrice: 80000,
    ),
    ProductModel(
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

  @override
  List<ProductModel> getProducts() {
    return _products;
  }

  @override
  ProductModel getProductById(String id) {
    return _products.firstWhere((product) => product.id == id);
  }

  @override
  void addProduct(ProductModel product) {
    _products.add(product);
  }

  @override
  void updateProduct(ProductModel product) {
    final index = _products.indexWhere((p) => p.id == product.id);
    if (index != -1) {
      _products[index] = product;
    }
  }
}
