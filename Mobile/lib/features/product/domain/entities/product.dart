class Product {
  final String id;
  final String name;
  final String category;
  final int stock;
  final int minStock;
  final String unit;
  final double buyPrice;
  final double sellPrice;
  final String? sku;
  final bool isActive;
  final String? stockId;
  final String? outletId;

  Product({
    required this.id,
    required this.name,
    required this.category,
    required this.stock,
    required this.minStock,
    required this.unit,
    required this.buyPrice,
    required this.sellPrice,
    this.sku,
    this.isActive = false,
    this.stockId,
    this.outletId,
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
    String? sku,
    bool? isActive,
    String? stockId,
    String? outletId,
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
      sku: sku ?? this.sku,
      isActive: isActive ?? this.isActive,
      stockId: stockId ?? this.stockId,
      outletId: outletId ?? this.outletId,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'category': category,
        'unit': unit,
        'sell_price': sellPrice,
        'buy_price': buyPrice,
        'is_active': isActive,
        'sku': sku,
        'stock_id': stockId,
        'outlet_id': outletId,
      };
}
