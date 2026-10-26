import '../../domain/entities/product.dart';
import '../../domain/repositories/product_repository.dart';
import '../datasources/product_local_datasource.dart';
import '../models/product_model.dart';

class ProductRepositoryImpl implements ProductRepository {
  final ProductLocalDataSource localDataSource;

  ProductRepositoryImpl(this.localDataSource);

  @override
  List<Product> getProducts() {
    return localDataSource.getProducts();
  }

  @override
  Product getProductById(String id) {
    return localDataSource.getProductById(id);
  }

  @override
  void addProduct(Product product) {
    localDataSource.addProduct(ProductModel.fromEntity(product));
  }

  @override
  void updateProduct(Product product) {
    localDataSource.updateProduct(ProductModel.fromEntity(product));
  }

  @override
  List<Product> getLowStockProducts() {
    return getProducts().where((product) => product.isLowStock).toList();
  }

  @override
  int getTotalProducts() {
    return getProducts().length;
  }

  @override
  int getTotalLowStock() {
    return getLowStockProducts().length;
  }

  @override
  int getTotalStock() {
    return getProducts().fold(0, (sum, product) => sum + product.stock);
  }
}
