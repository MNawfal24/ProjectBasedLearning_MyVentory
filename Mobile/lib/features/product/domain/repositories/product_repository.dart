import '../entities/product.dart';

abstract class ProductRepository {
  List<Product> getProducts();
  Product getProductById(String id);
  void addProduct(Product product);
  void updateProduct(Product product);
  List<Product> getLowStockProducts();
  int getTotalProducts();
  int getTotalLowStock();
  int getTotalStock();
}
