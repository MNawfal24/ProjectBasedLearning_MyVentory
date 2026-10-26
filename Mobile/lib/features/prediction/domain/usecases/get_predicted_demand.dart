import '../../../product/domain/entities/product.dart';

class GetPredictedDemand {
  int call(Product product) {
    switch (product.id) {
      case 'P001':
        return 30;
      case 'P002':
        return 18;
      case 'P003':
        return 14;
      case 'P004':
        return 12;
      case 'P005':
        return 9;
      default:
        return 10;
    }
  }
}
