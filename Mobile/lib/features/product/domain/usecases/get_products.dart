import 'package:myventory/features/product/domain/entities/product.dart';
import 'package:myventory/features/product/domain/repositories/product_repository.dart';

class GetProducts {
  final ProductRepository repository;

  GetProducts(this.repository);

  Future<List<Product>> call({String? outletId}) async {
    await repository.loadProducts(outletId: outletId);
    return repository.products;
  }
}
