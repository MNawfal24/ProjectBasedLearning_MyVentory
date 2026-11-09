import 'package:flutter/material.dart';

import '../../domain/entities/product.dart';
import '../../../../widgets/app_theme.dart';

class ProductFormPage extends StatefulWidget {
  final List<Product>? products;
  final Product? product;
  final Future<void> Function(Product)? onSave;

  const ProductFormPage({
    super.key,
    this.products,
    this.product,
    this.onSave,
  });

  @override
  State<ProductFormPage> createState() => _ProductFormPageState();
}

class _ProductFormPageState extends State<ProductFormPage> {
  final formKey = GlobalKey<FormState>();

  late TextEditingController nameController;
  late TextEditingController stockController;
  late TextEditingController minStockController;
  late TextEditingController buyPriceController;
  late TextEditingController sellPriceController;

  String category = 'Coffee';
  String unit = 'Kg';

  bool get isEdit => widget.product != null;

  @override
  void initState() {
    super.initState();

    final product = widget.product;

    nameController = TextEditingController(text: product?.name ?? '');
    stockController = TextEditingController(
      text: product?.stock.toString() ?? '',
    );
    minStockController = TextEditingController(
      text: product?.minStock.toString() ?? '',
    );
    buyPriceController = TextEditingController(
      text: product?.buyPrice != null ? product!.buyPrice.toStringAsFixed(0) : '',
    );
    sellPriceController = TextEditingController(
      text: product?.sellPrice != null ? product!.sellPrice.toStringAsFixed(0) : '',
    );

    category = product?.category ?? 'Coffee';
    unit = product?.unit ?? 'Kg';
  }

  @override
  void dispose() {
    nameController.dispose();
    stockController.dispose();
    minStockController.dispose();
    buyPriceController.dispose();
    sellPriceController.dispose();
    super.dispose();
  }

  Future<void> saveProduct() async {
    if (!formKey.currentState!.validate()) {
      return;
    }

    final product = Product(
      id: widget.product?.id ?? 'P${DateTime.now().millisecondsSinceEpoch}',
      name: nameController.text.trim(),
      category: category,
      stock: int.tryParse(stockController.text.trim()) ?? (widget.product?.stock ?? 0),
      minStock: int.tryParse(minStockController.text.trim()) ?? (widget.product?.minStock ?? 0),
      unit: unit,
      buyPrice: double.tryParse(buyPriceController.text.trim()) ?? 0.0,
      sellPrice: double.tryParse(sellPriceController.text.trim()) ?? 0.0,
      sku: widget.product?.sku,
      isActive: widget.product?.isActive ?? true,
      outletId: widget.product?.outletId,
      stockId: widget.product?.stockId,
    );

    if (widget.onSave != null) {
      await widget.onSave!(product);
    }

    if (mounted) {
      Navigator.pop(context, true);
    }
  }

  String? requiredValidator(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Field is required';
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final textFamily = Theme.of(context).textTheme.bodyMedium?.fontFamily ?? 'Poppins';

    return Scaffold(
      appBar: AppBar(
        title: Text(
          isEdit ? 'Edit Product' : 'Add Product',
          style: TextStyle(fontFamily: textFamily, fontWeight: FontWeight.bold),
        ),
      ),
      body: Form(
        key: formKey,
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 40),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextFormField(
                controller: nameController,
                validator: requiredValidator,
                style: TextStyle(fontFamily: textFamily),
                decoration: InputDecoration(
                  labelText: 'Product Name',
                  labelStyle: TextStyle(fontFamily: textFamily, color: AppTheme.textSecondary),
                  prefixIcon: const Icon(Icons.inventory_2_outlined, color: AppTheme.primary),
                  filled: true,
                  fillColor: Colors.white,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(16),
                    borderSide: BorderSide.none,
                  ),
                ),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                initialValue: category,
                style: TextStyle(fontFamily: textFamily, color: AppTheme.textPrimary),
                decoration: InputDecoration(
                  labelText: 'Category',
                  labelStyle: TextStyle(fontFamily: textFamily, color: AppTheme.textSecondary),
                  filled: true,
                  fillColor: Colors.white,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(16),
                    borderSide: BorderSide.none,
                  ),
                ),
                items: const [
                  'Coffee',
                  'Dairy',
                  'Sweetener',
                  'Ingredient',
                  'Other',
                ].map((item) {
                  return DropdownMenuItem(
                    value: item,
                    child: Text(item, style: TextStyle(fontFamily: textFamily)),
                  );
                }).toList(),
                onChanged: (value) {
                  if (value != null) {
                    setState(() {
                      category = value;
                    });
                  }
                },
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: stockController,
                      validator: requiredValidator,
                      keyboardType: TextInputType.number,
                      readOnly: isEdit,
                      enabled: !isEdit,
                      style: TextStyle(fontFamily: textFamily),
                      decoration: InputDecoration(
                        labelText: 'Current Stock',
                        labelStyle: TextStyle(fontFamily: textFamily, color: AppTheme.textSecondary),
                        helperText: isEdit ? 'Gunakan Stok Masuk/Keluar di detail' : null,
                        helperMaxLines: 2,
                        filled: true,
                        fillColor: isEdit ? const Color(0xFFF0F2F5) : Colors.white,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16),
                          borderSide: BorderSide.none,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextFormField(
                      controller: minStockController,
                      validator: requiredValidator,
                      keyboardType: TextInputType.number,
                      style: TextStyle(fontFamily: textFamily),
                      decoration: InputDecoration(
                        labelText: 'Minimum Stock',
                        labelStyle: TextStyle(fontFamily: textFamily, color: AppTheme.textSecondary),
                        filled: true,
                        fillColor: Colors.white,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16),
                          borderSide: BorderSide.none,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                initialValue: unit,
                style: TextStyle(fontFamily: textFamily, color: AppTheme.textPrimary),
                decoration: InputDecoration(
                  labelText: 'Unit',
                  labelStyle: TextStyle(fontFamily: textFamily, color: AppTheme.textSecondary),
                  filled: true,
                  fillColor: Colors.white,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(16),
                    borderSide: BorderSide.none,
                  ),
                ),
                items: const [
                  'Kg',
                  'Liter',
                  'Pcs',
                  'Pack',
                  'Box',
                ].map((item) {
                  return DropdownMenuItem(
                    value: item,
                    child: Text(item, style: TextStyle(fontFamily: textFamily)),
                  );
                }).toList(),
                onChanged: (value) {
                  if (value != null) {
                    setState(() {
                      unit = value;
                    });
                  }
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: buyPriceController,
                validator: requiredValidator,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                style: TextStyle(fontFamily: textFamily),
                decoration: InputDecoration(
                  labelText: 'Purchase Price',
                  labelStyle: TextStyle(fontFamily: textFamily, color: AppTheme.textSecondary),
                  prefixText: 'Rp ',
                  filled: true,
                  fillColor: Colors.white,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(16),
                    borderSide: BorderSide.none,
                  ),
                ),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: sellPriceController,
                validator: requiredValidator,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                style: TextStyle(fontFamily: textFamily),
                decoration: InputDecoration(
                  labelText: 'Selling Price',
                  labelStyle: TextStyle(fontFamily: textFamily, color: AppTheme.textSecondary),
                  prefixText: 'Rp ',
                  filled: true,
                  fillColor: Colors.white,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(16),
                    borderSide: BorderSide.none,
                  ),
                ),
              ),
              const SizedBox(height: 30),
              SizedBox(
                width: double.infinity,
                height: 52,
                child: FilledButton(
                  style: FilledButton.styleFrom(
                    backgroundColor: AppTheme.primary,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                  onPressed: saveProduct,
                  child: Text(
                    isEdit ? 'Save Changes' : 'Add Product',
                    style: TextStyle(
                      fontFamily: textFamily,
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
