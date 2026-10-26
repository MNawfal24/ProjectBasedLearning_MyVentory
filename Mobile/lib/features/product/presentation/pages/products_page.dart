import 'package:flutter/material.dart';

import '../../data/models/product_model.dart';
import '../bloc/product_bloc.dart';
import '../../../../widgets/app_theme.dart';
import '../../../../widgets/product_card.dart';
import 'product_detail_page.dart';
import 'product_form_page.dart';

class ProductsPage extends StatefulWidget {
  final ProductBloc bloc;

  const ProductsPage({
    super.key,
    required this.bloc,
  });

  @override
  State<ProductsPage> createState() => _ProductsPageState();
}

class _ProductsPageState extends State<ProductsPage> {
  final TextEditingController searchController = TextEditingController();

  String selectedFilter = 'All';

  @override
  void dispose() {
    searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final textFamily = Theme.of(context).textTheme.bodyMedium?.fontFamily ?? 'Poppins';

    return AnimatedBuilder(
      animation: widget.bloc,
      builder: (context, _) {
        final search = searchController.text.toLowerCase();

        final filteredProducts = widget.bloc.products.where((product) {
          final matchesSearch = product.name.toLowerCase().contains(search);

          bool matchesFilter = true;
          if (selectedFilter == 'Low Stock') {
            matchesFilter = product.isLowStock;
          } else if (selectedFilter == 'Safe Stock') {
            matchesFilter = !product.isLowStock && product.stock > 0;
          } else if (selectedFilter == 'Sold Stock') {
            matchesFilter = product.stock == 0;
          }

          return matchesSearch && matchesFilter;
        }).toList();

        return Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Color(0xFFEAF2FF),
                Color(0xFFF5F7FB),
              ],
            ),
          ),
          child: SafeArea(
            child: Scaffold(
              backgroundColor: Colors.transparent,
              body: Padding(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 90),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Products',
                              style: TextStyle(
                                fontSize: 28,
                                fontWeight: FontWeight.bold,
                                color: AppTheme.textPrimary,
                                fontFamily: textFamily,
                              ),
                            ),
                            const SizedBox(height: 5),
                            Text(
                              'Manage your inventory',
                              style: TextStyle(
                                color: AppTheme.textSecondary,
                                fontFamily: textFamily,
                              ),
                            ),
                          ],
                        ),
                        ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.primary,
                            foregroundColor: Colors.white,
                            elevation: 0,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(14),
                            ),
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                          ),
                          onPressed: () async {
                            await Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => ProductFormPage(
                                  products: widget.bloc.products.map((e) => ProductModel.fromEntity(e)).toList(),
                                ),
                              ),
                            );
                          },
                          icon: const Icon(Icons.add, size: 18),
                          label: Text(
                            'Add',
                            style: TextStyle(fontFamily: textFamily, fontWeight: FontWeight.w600),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),
                    TextField(
                      controller: searchController,
                      onChanged: (_) => setState(() {}),
                      style: TextStyle(fontFamily: textFamily),
                      decoration: InputDecoration(
                        hintText: 'Search products...',
                        hintStyle: TextStyle(
                          color: AppTheme.textSecondary,
                          fontFamily: textFamily,
                        ),
                        prefixIcon: const Icon(
                          Icons.search,
                          color: AppTheme.primary,
                        ),
                        filled: true,
                        fillColor: Colors.white,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16),
                          borderSide: BorderSide.none,
                        ),
                      ),
                    ),
                    const SizedBox(height: 15),
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: [
                      _buildChoiceChip('All', textFamily),
                          const SizedBox(width: 8),
                          _buildChoiceChip('Low Stock', textFamily),
                          const SizedBox(width: 8),
                          _buildChoiceChip('Safe Stock', textFamily),
                          const SizedBox(width: 8),
                          _buildChoiceChip('Sold Stock', textFamily),
                        ],
                      ),
                    ),
                    const SizedBox(height: 15),
                    Expanded(
                      child: filteredProducts.isEmpty
                          ? Center(
                              child: Text(
                                'No products found.',
                                style: TextStyle(
                                  color: AppTheme.textSecondary,
                                  fontFamily: textFamily,
                                ),
                              ),
                            )
                          : ListView.separated(
                              itemCount: filteredProducts.length,
                              separatorBuilder: (_, _) => const SizedBox(height: 10),
                              itemBuilder: (context, index) {
                                final product = filteredProducts[index];

                                return ProductCard(
                                  product: product,
                                  onTap: () {
                                    Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                        builder: (_) => ProductDetailPage(
                                          product: product,
                                        ),
                                      ),
                                    );
                                  },
                                );
                              },
                            ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildChoiceChip(String label, String textFamily) {
    final isSelected = selectedFilter == label;
    return ChoiceChip(
      label: Text(
        label,
        style: TextStyle(fontFamily: textFamily),
      ),
      selected: isSelected,
      selectedColor: AppTheme.primary.withValues(alpha: 0.12),
      checkmarkColor: AppTheme.primary,
      labelStyle: TextStyle(
        color: isSelected ? AppTheme.primary : AppTheme.textSecondary,
        fontWeight: FontWeight.w600,
        fontFamily: textFamily,
      ),
      onSelected: (_) {
        setState(() {
          selectedFilter = label;
        });
      },
    );
  }
}
