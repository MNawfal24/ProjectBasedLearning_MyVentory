class Product {
  final String id;
  String name;
  String category;
  int stock;
  int minStock;
  String unit;
  double buyPrice;
  double sellPrice;

  Product({
    required this.id,
    required this.name,
    required this.category,
    required this.stock,
    required this.minStock,
    required this.unit,
    required this.buyPrice,
    required this.sellPrice,
  });

  bool get isLowStock => stock <= minStock;

  Product copyWith({
    String? id,
    String? name,
    String? category,
    int? stock,
    int? minStock,
    String? unit,
    double? buyPrice,
    double? sellPrice,
  }) {
    return Product(
      id: id ?? this.id,
      name: name ?? this.name,
      category: category ?? this.category,
      stock: stock ?? this.stock,
      minStock: minStock ?? this.minStock,
      unit: unit ?? this.unit,
      buyPrice: buyPrice ?? this.buyPrice,
      sellPrice: sellPrice ?? this.sellPrice,
    );
  }
}