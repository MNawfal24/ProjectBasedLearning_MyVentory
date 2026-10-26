import '../repositories/product_repository.dart';

class GetProductStats {
  final ProductRepository repository;

  GetProductStats(this.repository);

  Map<String, int> call() {
    return {
      'totalProducts': repository.getTotalProducts(),
      'totalLowStock': repository.getTotalLowStock(),
      'totalStock': repository.getTotalStock(),
    };
  }
}
