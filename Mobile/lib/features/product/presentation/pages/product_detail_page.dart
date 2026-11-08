import 'package:flutter/material.dart';

import 'package:myventory/data/mock_data.dart';
import 'package:myventory/features/product/domain/entities/product.dart';
import 'package:myventory/widgets/app_theme.dart';
import 'package:myventory/features/product/presentation/pages/product_form_page.dart';

class ProductDetailPage extends StatelessWidget {
  final Product product;
  final InventoryStore? store;
  final Future<void> Function(Product)? onSave;

  const ProductDetailPage({
    super.key,
    required this.product,
    this.store,
    this.onSave,
  });

  String currency(double value) {
    return 'Rp ${value.toStringAsFixed(0)}';
  }

  Future<void> _edit(BuildContext context) async {
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ProductFormPage(
          product: product,
          onSave: onSave,
        ),
      ),
    );
  }

  Future<void> _confirmDelete(BuildContext context) async {
    if (store == null) return;
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Hapus Produk?'),
        content: Text('Produk ${product.name} akan dihapus dari server.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Batal'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            style: FilledButton.styleFrom(backgroundColor: AppTheme.danger),
            child: const Text('Hapus'),
          ),
        ],
      ),
    );
    if (ok == true && context.mounted) {
      await store!.deleteProduct(product.id);
      if (context.mounted) Navigator.pop(context, true);
    }
  }

  Future<void> _adjustStock(BuildContext context, String type) async {
    if (store == null) return;
    final qtyCtrl = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(type == 'in' ? 'Stok Masuk' : 'Stok Keluar'),
        content: TextField(
          controller: qtyCtrl,
          keyboardType: TextInputType.number,
          decoration: InputDecoration(
            labelText: 'Jumlah (${product.unit})',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Batal'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Simpan'),
          ),
        ],
      ),
    );
    if (ok == true && context.mounted) {
      final quantity = double.tryParse(qtyCtrl.text.trim()) ?? 0;
      if (quantity <= 0) return;
      await store!.adjustStock(
        outletId: product.outletId ?? '',
        productId: product.id,
        type: type,
        quantity: quantity,
        note: 'Penyesuaian dari detail produk',
      );
    }
  }

  Future<void> _setMinStock(BuildContext context) async {
    if (store == null || product.stockId == null) return;
    final qtyCtrl = TextEditingController(text: product.minStock.toString());
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Batas Minimum Stok'),
        content: TextField(
          controller: qtyCtrl,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(labelText: 'Minimum'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Batal'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Simpan'),
          ),
        ],
      ),
    );
    if (ok == true && context.mounted) {
      await store!.setMinStock(
        product.stockId!,
        double.tryParse(qtyCtrl.text.trim()) ?? 0,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
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
        actions: [
          if (store != null)
            IconButton(
              icon: const Icon(Icons.delete_outline, color: AppTheme.danger),
              onPressed: () => _confirmDelete(context),
              tooltip: 'Hapus',
            ),
          IconButton(
            icon: const Icon(Icons.edit_outlined),
            onPressed: () => _edit(context),
            tooltip: 'Edit',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            _buildHeader(stockLabel, stockColor, isOutOfStock),
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
            _buildPriceCard(),
            const SizedBox(height: 15),
            _buildActionButtons(context),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(String stockLabel, Color stockColor, bool isOutOfStock) {
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

  Widget _buildPriceCard() {
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

  Widget _buildActionButtons(BuildContext context) {
    return Column(
      children: [
        SizedBox(
          width: double.infinity,
          child: FilledButton.icon(
            onPressed: () => _edit(context),
            icon: const Icon(Icons.edit),
            label: const Text('Edit Product'),
          ),
        ),
        const SizedBox(height: 10),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            onPressed: () => _adjustStock(context, 'in'),
            icon: const Icon(Icons.add_circle_outline),
            label: const Text('Stok Masuk'),
          ),
        ),
        const SizedBox(height: 10),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            onPressed: () => _adjustStock(context, 'out'),
            icon: const Icon(Icons.remove_circle_outline),
            label: const Text('Stok Keluar'),
          ),
        ),
        const SizedBox(height: 10),
        if (product.stockId != null)
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () => _setMinStock(context),
              icon: const Icon(Icons.warning_amber_outlined),
              label: const Text('Atur Minimum Stok'),
            ),
          ),
        const SizedBox(height: 10),
      ],
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
