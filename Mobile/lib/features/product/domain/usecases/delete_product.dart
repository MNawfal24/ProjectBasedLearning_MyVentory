import 'package:myventory/features/product/domain/repositories/product_repository.dart';

class DeleteProduct {
  final ProductRepository repository;

  DeleteProduct(this.repository);

  Future<void> call(String id) async => repository.deleteProduct(id);
}
