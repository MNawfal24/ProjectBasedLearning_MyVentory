import 'package:flutter/material.dart';

import 'package:myventory/data/mock_data.dart';
import 'package:myventory/features/product/domain/entities/product.dart';
import 'package:myventory/widgets/app_theme.dart';

class ProductDetailPage extends StatefulWidget {
  final Product product;
  final InventoryStore? store;

  const ProductDetailPage({
    super.key,
    required this.product,
    this.store,
  });

  @override
  State<ProductDetailPage> createState() => _ProductDetailPageState();
}

class _ProductDetailPageState extends State<ProductDetailPage> {
  late Product _product;

  @override
  void initState() {
    super.initState();
    _product = widget.product;
  }

  Product get currentProduct =>
      widget.store?.getProductById(_product.id) ?? _product;

  String currency(double value) {
    return 'Rp ${value.toStringAsFixed(0)}';
  }

  @override
  Widget build(BuildContext context) {
    if (widget.store != null) {
      return AnimatedBuilder(
        animation: widget.store!,
        builder: (context, _) => _buildScaffold(context, currentProduct),
      );
    }
    return _buildScaffold(context, currentProduct);
  }

  Widget _buildScaffold(BuildContext context, Product product) {
    final bool isOutOfStock = product.stock == 0;
    final bool isLowStock = !isOutOfStock && product.isLowStock;

    String stockLabel;
    Color stockColor;

    if (isOutOfStock) {
      stockLabel = 'Out of Stock (Kosong)';
      stockColor = Colors.grey.shade700;
    } else if (isLowStock) {
      stockLabel = 'Low Stock';
      stockColor = AppTheme.danger;
    } else {
      stockLabel = 'Stock Available';
      stockColor = AppTheme.secondary;
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Product Detail'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            _buildHeader(product, stockLabel, stockColor, isOutOfStock),
            const SizedBox(height: 15),
            Row(
              children: [
                Expanded(
                  child: _InfoCard(
                    title: 'Current Stock',
                    value: '${product.stock} ${product.unit}',
                    icon: Icons.inventory_2_outlined,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _InfoCard(
                    title: 'Minimum Stock',
                    value: '${product.minStock} ${product.unit}',
                    icon: Icons.warning_amber_outlined,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 15),
            _buildPriceCard(product),
            const SizedBox(height: 15),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.primary.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline, color: AppTheme.primary),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Perubahan stok, harga, dan batas minimum dilakukan dari dashboard web.',
                      style: TextStyle(
                        fontSize: 12,
                        color: AppTheme.textPrimary,
                        fontFamily:
                            Theme.of(context).textTheme.bodyMedium?.fontFamily ??
                                'Poppins',
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(Product product, String stockLabel, Color stockColor, bool isOutOfStock) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(25),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        children: [
          Container(
            width: 85,
            height: 85,
            decoration: BoxDecoration(
              color: stockColor.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Icon(
              isOutOfStock ? Icons.remove_shopping_cart_outlined : Icons.inventory_2_outlined,
              size: 42,
              color: stockColor,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            product.name,
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 6),
          Text(
            product.category,
            style: const TextStyle(color: Colors.grey),
          ),
          const SizedBox(height: 15),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
            decoration: BoxDecoration(
              color: stockColor.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(30),
            ),
            child: Text(
              stockLabel,
              style: TextStyle(color: stockColor, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPriceCard(Product product) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Price Information',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 18),
          _PriceRow(label: 'Purchase Price', value: currency(product.buyPrice)),
          const SizedBox(height: 12),
          _PriceRow(label: 'Selling Price', value: currency(product.sellPrice)),
        ],
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;

  const _InfoCard({
    required this.title,
    required this.value,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: AppTheme.primary),
          const SizedBox(height: 14),
          Text(
            title,
            style: const TextStyle(color: Colors.grey, fontSize: 12),
          ),
          const SizedBox(height: 5),
          Text(
            value,
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }
}

class _PriceRow extends StatelessWidget {
  final String label;
  final String value;

  const _PriceRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(color: Colors.grey)),
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
      ],
    );
  }
}
