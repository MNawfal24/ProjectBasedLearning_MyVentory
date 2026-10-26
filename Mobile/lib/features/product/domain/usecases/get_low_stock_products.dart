import '../entities/product.dart';
import '../repositories/product_repository.dart';

class GetLowStockProducts {
  final ProductRepository repository;

  GetLowStockProducts(this.repository);

  List<Product> call() {
    return repository.getLowStockProducts();
  }
}
