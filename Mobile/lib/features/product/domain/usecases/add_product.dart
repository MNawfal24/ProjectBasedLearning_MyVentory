import 'package:myventory/features/product/domain/entities/product.dart';
import 'package:myventory/features/product/domain/repositories/product_repository.dart';

class AddProduct {
  final ProductRepository repository;

  AddProduct(this.repository);

  Future<Product> call(Product product) async =>
      repository.addProduct(product);
}
