import 'package:myventory/features/product/domain/entities/product.dart';

/// Kontrak repositori produk. Baca data dari cache internal yang diisi oleh
/// [loadProducts]; semua tulisan (tambah/ubah/hapus/stok) dikirim ke API Laravel.
abstract class ProductRepository {
  List<Product> get products;
  List<Product> getLowStockProducts();
  int getTotalProducts();
  int getTotalLowStock();
  int getTotalStock();

  Future<void> loadProducts({String? outletId});
  Future<Product> getProductById(String id, {String? outletId});
  Future<Product> addProduct(Product product);
  Future<Product> updateProduct(Product product);
  Future<void> deleteProduct(String id);
  Future<void> adjustStock({
    required String outletId,
    required String productId,
    required String type,
    required double quantity,
    String? note,
  });
  Future<void> setMinStock(String stockId, double minQuantity);
}
