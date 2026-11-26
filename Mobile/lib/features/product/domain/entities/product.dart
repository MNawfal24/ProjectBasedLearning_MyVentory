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
  final String? supplierName;
  final String? supplierPhone;

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
    this.supplierName,
    this.supplierPhone,
  });

  bool get isLowStock => stock <= minStock;

  bool get hasSupplier =>
      (supplierName?.trim().isNotEmpty ?? false) ||
      (supplierPhone?.trim().isNotEmpty ?? false);

  String? get supplierWhatsappNumber {
    final digits = (supplierPhone ?? '').replaceAll(RegExp(r'\D'), '');
    if (digits.isEmpty) return null;
    if (digits.startsWith('62')) return digits;
    if (digits.startsWith('0')) return '62${digits.substring(1)}';
    if (digits.startsWith('8')) return '62$digits';
    return digits;
  }

  Uri? get supplierWhatsappUri {
    final number = supplierWhatsappNumber;
    if (number == null) return null;
    return Uri.parse('https://wa.me/$number');
  }

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
    String? supplierName,
    String? supplierPhone,
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
      supplierName: supplierName ?? this.supplierName,
      supplierPhone: supplierPhone ?? this.supplierPhone,
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
        'supplier_name': supplierName,
        'supplier_phone': supplierPhone,
      };
}
