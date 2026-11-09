import 'package:myventory/features/product/domain/entities/product.dart';
import 'package:myventory/features/product/domain/repositories/product_repository.dart';

class GetProductById {
  final ProductRepository repository;

  GetProductById(this.repository);

  Future<Product> call(String id, {String? outletId}) async =>
      repository.getProductById(id, outletId: outletId);
}
