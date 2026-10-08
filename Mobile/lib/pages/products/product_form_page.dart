import 'package:flutter/material.dart';

import '../../data/mock_data.dart';
import '../../models/product_model.dart';
import '../../widgets/app_theme.dart';

class ProductFormPage extends StatefulWidget {
  final InventoryStore store;
  final Product? product;

  const ProductFormPage({
    super.key,
    required this.store,
    this.product,
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

  void saveProduct() {
    if (!formKey.currentState!.validate()) {
      return;
    }

    final product = Product(
      id: widget.product?.id ?? 'P${DateTime.now().millisecondsSinceEpoch}',
      name: nameController.text.trim(),
      category: category,
      stock: int.parse(stockController.text.trim()),
      minStock: int.parse(minStockController.text.trim()),
      unit: unit,
      buyPrice: double.parse(buyPriceController.text.trim()),
      sellPrice: double.parse(sellPriceController.text.trim()),
    );

    if (isEdit) {
      widget.store.updateProduct(product);
    } else {
      widget.store.addProduct(product);
    }

    Navigator.pop(context);

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          isEdit ? 'Product updated successfully' : 'Product added successfully',
        ),
      ),
    );
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
                value: category,
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
                      style: TextStyle(fontFamily: textFamily),
                      decoration: InputDecoration(
                        labelText: 'Current Stock',
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
                value: unit,
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