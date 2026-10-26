import '../../../product/domain/entities/product.dart';
import 'get_predicted_demand.dart';

class GetRecommendedRestock {
  final GetPredictedDemand getPredictedDemand;

  GetRecommendedRestock(this.getPredictedDemand);

  int call(Product product) {
    final demand = getPredictedDemand(product);
    const safetyStock = 5;
    final recommendation = (demand + safetyStock - product.stock).toInt();
    return recommendation > 0 ? recommendation : 0;
  }
}
