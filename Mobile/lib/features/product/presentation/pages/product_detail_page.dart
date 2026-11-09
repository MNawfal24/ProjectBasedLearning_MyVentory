import 'package:flutter/material.dart';

import 'package:myventory/data/mock_data.dart';
import 'package:myventory/features/product/domain/entities/product.dart';
import 'package:myventory/widgets/app_theme.dart';
import 'package:myventory/features/product/presentation/pages/product_form_page.dart';

class ProductDetailPage extends StatefulWidget {
  final Product product;
  final InventoryStore? store;
  final Future<void> Function(Product)? onSave;

  const ProductDetailPage({
    super.key,
    required this.product,
    this.store,
    this.onSave,
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

  Future<void> _edit(BuildContext context) async {
    final fresh = currentProduct;
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ProductFormPage(
          product: fresh,
          onSave: (updated) async {
            if (widget.onSave != null) {
              await widget.onSave!(updated);
              if (mounted) {
                if (widget.store?.error != null) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(widget.store!.error!),
                      backgroundColor: AppTheme.danger,
                    ),
                  );
                } else {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Produk berhasil diperbarui.'),
                      backgroundColor: AppTheme.secondary,
                    ),
                  );
                }
              }
            }
          },
        ),
      ),
    );
  }

  Future<void> _confirmDelete(BuildContext context) async {
    if (widget.store == null) return;
    final prod = currentProduct;
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Hapus Produk?'),
        content: Text('Produk ${prod.name} akan dihapus dari server.'),
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
    if (ok == true && mounted) {
      await widget.store!.deleteProduct(prod.id);
      if (!mounted) return;

      if (widget.store!.error != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(widget.store!.error!),
            backgroundColor: AppTheme.danger,
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Produk ${prod.name} berhasil dihapus.'),
            backgroundColor: AppTheme.secondary,
          ),
        );
        Navigator.pop(context, true);
      }
    }
  }

  Future<void> _adjustStock(BuildContext context, String type) async {
    if (widget.store == null) return;
    final prod = currentProduct;
    final qtyCtrl = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(type == 'in' ? 'Stok Masuk' : 'Stok Keluar'),
        content: TextField(
          controller: qtyCtrl,
          keyboardType: TextInputType.number,
          decoration: InputDecoration(
            labelText: 'Jumlah (${prod.unit})',
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
    if (ok == true && mounted) {
      final quantity = double.tryParse(qtyCtrl.text.trim()) ?? 0;
      if (quantity <= 0) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Jumlah harus lebih dari nol.'),
            backgroundColor: AppTheme.danger,
          ),
        );
        return;
      }

      await widget.store!.adjustStock(
        outletId: prod.outletId ?? '',
        productId: prod.id,
        type: type,
        quantity: quantity,
        note: 'Penyesuaian dari detail produk',
      );

      if (!mounted) return;

      if (widget.store!.error != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(widget.store!.error!),
            backgroundColor: AppTheme.danger,
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              type == 'in'
                  ? 'Stok masuk berhasil dicatat.'
                  : 'Stok keluar berhasil dicatat.',
            ),
            backgroundColor: AppTheme.secondary,
          ),
        );
      }
    }
  }

  Future<void> _setMinStock(BuildContext context) async {
    if (widget.store == null) return;
    final prod = currentProduct;
    if (prod.stockId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Identitas stok belum tersedia.'),
          backgroundColor: AppTheme.danger,
        ),
      );
      return;
    }

    final qtyCtrl = TextEditingController(text: prod.minStock.toString());
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
    if (ok == true && mounted) {
      final minQuantity = double.tryParse(qtyCtrl.text.trim()) ?? 0;
      await widget.store!.setMinStock(prod.stockId!, minQuantity);

      if (!mounted) return;

      if (widget.store!.error != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(widget.store!.error!),
            backgroundColor: AppTheme.danger,
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Batas minimum stok berhasil diperbarui.'),
            backgroundColor: AppTheme.secondary,
          ),
        );
      }
    }
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
        actions: [
          if (widget.store != null)
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
            _buildActionButtons(context, product),
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

  Widget _buildActionButtons(BuildContext context, Product product) {
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
