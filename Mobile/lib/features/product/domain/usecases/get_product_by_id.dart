import '../entities/product.dart';
import '../repositories/product_repository.dart';

class GetProductById {
  final ProductRepository repository;

  GetProductById(this.repository);

  Product call(String id) {
    return repository.getProductById(id);
  }
}
