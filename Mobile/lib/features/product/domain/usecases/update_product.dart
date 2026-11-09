import 'package:myventory/features/product/domain/entities/product.dart';
import 'package:myventory/features/product/domain/repositories/product_repository.dart';

class UpdateProduct {
  final ProductRepository repository;

  UpdateProduct(this.repository);

  Future<Product> call(Product product) async =>
      repository.updateProduct(product);
}
