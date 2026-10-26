import '../../domain/entities/product.dart';

class ProductModel extends Product {
  ProductModel({
    required super.id,
    required super.name,
    required super.category,
    required super.stock,
    required super.minStock,
    required super.unit,
    required super.buyPrice,
    required super.sellPrice,
  });

  factory ProductModel.fromEntity(Product product) {
    return ProductModel(
      id: product.id,
      name: product.name,
      category: product.category,
      stock: product.stock,
      minStock: product.minStock,
      unit: product.unit,
      buyPrice: product.buyPrice,
      sellPrice: product.sellPrice,
    );
  }

  Product toEntity() {
    return Product(
      id: id,
      name: name,
      category: category,
      stock: stock,
      minStock: minStock,
      unit: unit,
      buyPrice: buyPrice,
      sellPrice: sellPrice,
    );
  }
}
