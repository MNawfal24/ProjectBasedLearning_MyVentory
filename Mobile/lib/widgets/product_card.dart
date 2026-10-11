import 'package:flutter/material.dart';

import '../models/product_model.dart';
import 'app_theme.dart';

class ProductCard extends StatelessWidget {
  final Product product;
  final VoidCallback onTap;

  const ProductCard({
    super.key,
    required this.product,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final textFamily = Theme.of(context).textTheme.bodyMedium?.fontFamily ?? 'Poppins';

    final bool isOutOfStock = product.stock == 0;
    final bool isLowStock = !isOutOfStock && product.isLowStock;

    Color statusColor;
    String statusLabel;
    IconData statusIcon;

    if (isOutOfStock) {
      statusColor = Colors.grey.shade700;
      statusLabel = 'Out of Stock';
      statusIcon = Icons.remove_shopping_cart_outlined;
    } else if (isLowStock) {
      statusColor = AppTheme.danger;
      statusLabel = 'Low Stock';
      statusIcon = Icons.warning_amber_outlined;
    } else {
      statusColor = AppTheme.secondary;
      statusLabel = 'Available';
      statusIcon = Icons.inventory_2_outlined;
    }

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(18),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.02),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              width: 55,
              height: 55,
              decoration: BoxDecoration(
                color: statusColor.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Icon(
                statusIcon,
                color: statusColor,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    product.name,
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 15,
                      color: AppTheme.textPrimary,
                      fontFamily: textFamily,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    product.category,
                    style: TextStyle(
                      color: AppTheme.textSecondary,
                      fontSize: 12,
                      fontFamily: textFamily,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Text(
                        '${product.stock} ${product.unit}',
                        style: TextStyle(
                          fontWeight: FontWeight.w700,
                          color: statusColor,
                          fontFamily: textFamily,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: statusColor.withValues(alpha: 0.10),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          statusLabel,
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w700,
                            color: statusColor,
                            fontFamily: textFamily,
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const Icon(
              Icons.chevron_right,
              color: AppTheme.textSecondary,
            ),
          ],
        ),
      ),
    );
  }
}