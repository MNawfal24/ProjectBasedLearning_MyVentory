import 'package:flutter/material.dart';

import '../../data/mock_data.dart';
import '../../models/product_model.dart';
import '../../widgets/app_theme.dart';

class StockoutPage extends StatelessWidget {
  final InventoryStore store;
  final Product product;

  const StockoutPage({
    super.key,
    required this.store,
    required this.product,
  });

  @override
  Widget build(BuildContext context) {
    final demand = store.predictedDemand(product);
    const safetyStock = 5;
    final restock = store.recommendedRestock(product);

    final risk = product.stock < demand;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Stock-out Analysis'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(22),
              decoration: BoxDecoration(
                color: risk
                    ? AppTheme.danger.withValues(alpha: 0.08)
                    : AppTheme.secondary.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Column(
                children: [
                  Icon(
                    risk
                        ? Icons.warning_amber_rounded
                        : Icons.check_circle_outline,
                    size: 50,
                    color: risk
                        ? AppTheme.danger
                        : AppTheme.secondary,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    product.name,
                    style: const TextStyle(
                      fontSize: 21,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    risk
                        ? 'Potential stock-out detected'
                        : 'Stock level is sufficient',
                    style: TextStyle(
                      color: risk
                          ? AppTheme.danger
                          : AppTheme.secondary,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 18),

            _AnalysisRow(
              label: 'Current Stock',
              value:
                  '${product.stock} ${product.unit}',
            ),
            _AnalysisRow(
              label: 'Predicted Demand',
              value:
                  '$demand ${product.unit}',
            ),
            _AnalysisRow(
              label: 'Safety Stock',
              value:
                  '$safetyStock ${product.unit}',
            ),
            _AnalysisRow(
              label: 'Recommended Restock',
              value:
                  '$restock ${product.unit}',
              highlight: true,
            ),

            const SizedBox(height: 20),

            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(18),
              ),
              child: Column(
                crossAxisAlignment:
                    CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Calculation',
                    style: TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 15),
                  Text(
                    'Restock = Predicted Demand + Safety Stock - Current Stock',
                    style: TextStyle(
                      color: Colors.grey.shade700,
                      height: 1.5,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    '$demand + $safetyStock - ${product.stock} = $restock ${product.unit}',
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
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
}

class _AnalysisRow extends StatelessWidget {
  final String label;
  final String value;
  final bool highlight;

  const _AnalysisRow({
    required this.label,
    required this.value,
    this.highlight = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        mainAxisAlignment:
            MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(
              color: Colors.grey,
            ),
          ),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: highlight
                  ? AppTheme.primary
                  : Colors.black,
            ),
          ),
        ],
      ),
    );
  }
}