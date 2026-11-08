import 'features/prediction/domain/usecases/get_predicted_demand.dart';
import 'features/prediction/domain/usecases/get_recommended_restock.dart';
import 'features/product/data/datasources/product_local_datasource.dart';
import 'features/product/data/repositories/product_repository_impl.dart';
import 'features/product/domain/repositories/product_repository.dart';
import 'features/product/domain/usecases/add_product.dart';
import 'features/product/domain/usecases/get_low_stock_products.dart';
import 'features/product/domain/usecases/get_product_by_id.dart';
import 'features/product/domain/usecases/get_product_stats.dart';
import 'features/product/domain/usecases/get_products.dart';
import 'features/product/domain/usecases/update_product.dart';

class InjectionContainer {
  static final InjectionContainer _instance = InjectionContainer._internal();
  factory InjectionContainer() => _instance;
  InjectionContainer._internal();

  late final ProductLocalDataSource productLocalDataSource;
  late final ProductRepository productRepository;

  late final GetProducts getProducts;
  late final GetProductById getProductById;
  late final AddProduct addProduct;
  late final UpdateProduct updateProduct;
  late final GetLowStockProducts getLowStockProducts;
  late final GetProductStats getProductStats;

  late final GetPredictedDemand getPredictedDemand;
  late final GetRecommendedRestock getRecommendedRestock;

  void init() {
    productLocalDataSource = ProductLocalDataSourceImpl();
    productRepository = ProductRepositoryImpl(productLocalDataSource);

    getProducts = GetProducts(productRepository);
    getProductById = GetProductById(productRepository);
    addProduct = AddProduct(productRepository);
    updateProduct = UpdateProduct(productRepository);
    getLowStockProducts = GetLowStockProducts(productRepository);
    getProductStats = GetProductStats(productRepository);

    getPredictedDemand = GetPredictedDemand();
    getRecommendedRestock = GetRecommendedRestock(getPredictedDemand);
  }
}

final sl = InjectionContainer();
