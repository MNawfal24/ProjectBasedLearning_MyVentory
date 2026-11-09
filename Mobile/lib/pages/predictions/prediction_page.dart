import 'package:flutter/material.dart';

import '../../data/mock_data.dart';
import '../../features/product/domain/entities/product.dart';
import '../../widgets/app_theme.dart';
import 'stockout_page.dart';

class PredictionPage extends StatefulWidget {
  final InventoryStore store;

  const PredictionPage({
    super.key,
    required this.store,
  });

  @override
  State<PredictionPage> createState() => _PredictionPageState();
}

class _PredictionPageState extends State<PredictionPage> {
  String? selectedProductId;
  final Set<String> _requested = {};

  void _ensureForecast(Product product) {
    if (_requested.contains(product.id)) return;
    _requested.add(product.id);
    widget.store.fetchDemand(product);
  }

  @override
  void initState() {
    super.initState();
  }

  void _showAllPredictions(BuildContext context, String textFamily) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) {
        return Container(
          height: MediaQuery.of(context).size.height * 0.75,
          padding: const EdgeInsets.all(20),
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Colors.grey[300],
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'All Products Demand Forecast',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.textPrimary,
                  fontFamily: textFamily,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Predicted demand for the next 7 days across all inventory',
                style: TextStyle(
                  fontSize: 12,
                  color: AppTheme.textSecondary,
                  fontFamily: textFamily,
                ),
              ),
              const SizedBox(height: 16),
              Expanded(
                child: widget.store.products.isEmpty
                    ? Center(
                        child: Text(
                          'No products available for prediction',
                          style: TextStyle(
                            color: AppTheme.textSecondary,
                            fontFamily: textFamily,
                          ),
                        ),
                      )
                    : ListView.builder(
                        itemCount: widget.store.products.length,
                        itemBuilder: (context, index) {
                          final product = widget.store.products[index];
                          _ensureForecast(product);
                          final productDemand = widget.store.predictedDemand(product);
                          
                          return Container(
                            margin: const EdgeInsets.only(bottom: 12),
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: const Color(0xFFF9FAFC),
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(color: Colors.grey.shade200),
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        product.name,
                                        style: TextStyle(
                                          fontWeight: FontWeight.bold,
                                          fontSize: 15,
                                          color: AppTheme.textPrimary,
                                          fontFamily: textFamily,
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        'Current Stock: ${product.stock} ${product.unit}',
                                        style: TextStyle(
                                          fontSize: 12,
                                          color: AppTheme.textSecondary,
                                          fontFamily: textFamily,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                  decoration: BoxDecoration(
                                    color: AppTheme.primary.withValues(alpha: 0.1),
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.end,
                                    children: [
                                      Text(
                                        '$productDemand',
                                        style: TextStyle(
                                          fontWeight: FontWeight.bold,
                                          fontSize: 16,
                                          color: AppTheme.primary,
                                          fontFamily: textFamily,
                                        ),
                                      ),
                                      Text(
                                        'Predicted',
                                        style: TextStyle(
                                          fontSize: 10,
                                          color: AppTheme.textSecondary,
                                          fontFamily: textFamily,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          );
                        },
                      ),
              ),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final textFamily = Theme.of(context).textTheme.bodyMedium?.fontFamily ?? 'Poppins';

    return AnimatedBuilder(
      animation: widget.store,
      builder: (context, _) {
        final products = widget.store.products;

        // 1. Loading state: jika data produk sedang dimuat dan belum ada produk
        if (widget.store.loading && products.isEmpty) {
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
            child: const SafeArea(
              child: Center(
                child: CircularProgressIndicator(color: AppTheme.primary),
              ),
            ),
          );
        }

        // 2. Empty state: jika data produk kosong
        if (products.isEmpty) {
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
              child: Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 32.0),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.inventory_2_outlined,
                        size: 72,
                        color: AppTheme.textSecondary.withValues(alpha: 0.5),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'Belum Ada Produk',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.textPrimary,
                          fontFamily: textFamily,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Tambahkan produk terlebih dahulu untuk melihat prediksi permintaan dan analisis stok.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontSize: 14,
                          color: AppTheme.textSecondary,
                          fontFamily: textFamily,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          );
        }

        // 3. Products available: tentukan produk yang valid secara aman
        Product activeProduct;
        try {
          activeProduct = products.firstWhere(
            (p) => p.id == selectedProductId,
          );
        } catch (_) {
          activeProduct = products.first;
        }

        final demand = widget.store.predictedDemand(activeProduct);
        _ensureForecast(activeProduct);

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
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 100),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Prediction',
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.textPrimary,
                      fontFamily: textFamily,
                    ),
                  ),
                  const SizedBox(height: 5),
                  Text(
                    'Demand forecasting & inventory insights',
                    style: TextStyle(
                      color: AppTheme.textSecondary,
                      fontFamily: textFamily,
                    ),
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    height: 52,
                    child: OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: AppTheme.primary),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                      ),
                      onPressed: () => _showAllPredictions(context, textFamily),
                      icon: const Icon(Icons.list_alt_rounded, color: AppTheme.primary),
                      label: Text(
                        'View All Products Prediction',
                        style: TextStyle(
                          color: AppTheme.primary,
                          fontFamily: textFamily,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 22),
                  DropdownButtonFormField<String>(
                    key: ValueKey(activeProduct.id),
                    initialValue: activeProduct.id,
                    decoration: InputDecoration(
                      labelText: 'Select Product',
                      labelStyle: TextStyle(
                        color: AppTheme.textSecondary,
                        fontFamily: textFamily,
                      ),
                      filled: true,
                      fillColor: Colors.white,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16),
                        borderSide: BorderSide.none,
                      ),
                    ),
                    items: products.map((product) {
                      return DropdownMenuItem<String>(
                        value: product.id,
                        child: Text(
                          product.name,
                          style: TextStyle(fontFamily: textFamily),
                        ),
                      );
                    }).toList(),
                    onChanged: (productId) {
                      setState(() {
                        selectedProductId = productId;
                      });
                    },
                  ),
                  const SizedBox(height: 20),
                  Row(
                    children: [
                      Expanded(
                        child: _PredictionCard(
                          title: 'Current Stock',
                          value: '${activeProduct.stock}',
                          subtitle: activeProduct.unit,
                          icon: Icons.inventory_2_outlined,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: _PredictionCard(
                          title: 'Predicted Demand',
                          value: '$demand',
                          subtitle: 'Next 7 days',
                          icon: Icons.trending_up,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.02),
                          blurRadius: 8,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '7-Day Demand Forecast',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 17,
                            color: AppTheme.textPrimary,
                            fontFamily: textFamily,
                          ),
                        ),
                        const SizedBox(height: 5),
                        Text(
                          'Prediksi permintaan dari model ML',
                          style: TextStyle(
                            color: AppTheme.textSecondary,
                            fontSize: 12,
                            fontFamily: textFamily,
                          ),
                        ),
                        const SizedBox(height: 25),
                        SizedBox(
                          height: 220,
                          child: _DemandChart(
                            points: widget.store.demandSeries(activeProduct),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: AppTheme.primary.withValues(alpha: 0.08),
                      borderRadius: BorderRadius.circular(18),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.auto_awesome, color: AppTheme.primary),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Text(
                            'Prediksi dihitung model ML di server. Stok dan batas minimum tetap dikelola dari dashboard web.',
                            style: TextStyle(
                              fontSize: 13,
                              color: AppTheme.textPrimary,
                              fontFamily: textFamily,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                  SizedBox(
                    width: double.infinity,
                    height: 52,
                    child: FilledButton.icon(
                      style: FilledButton.styleFrom(
                        backgroundColor: AppTheme.primary,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                      ),
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => StockoutPage(
                              product: activeProduct,
                              demand: demand,
                            ),
                          ),
                        );
                      },
                      icon: const Icon(Icons.warning_amber_rounded),
                      label: Text(
                        'View Stock-out Analysis',
                        style: TextStyle(fontFamily: textFamily),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class _PredictionCard extends StatelessWidget {
  final String title;
  final String value;
  final String subtitle;
  final IconData icon;

  const _PredictionCard({
    required this.title,
    required this.value,
    required this.subtitle,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    final textFamily = Theme.of(context).textTheme.bodyMedium?.fontFamily ?? 'Poppins';

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
          const SizedBox(height: 12),
          Text(
            title,
            style: TextStyle(
              fontSize: 12,
              color: AppTheme.textSecondary,
              fontFamily: textFamily,
            ),
          ),
          const SizedBox(height: 5),
          Text(
            value,
            style: TextStyle(
              fontSize: 23,
              fontWeight: FontWeight.bold,
              color: AppTheme.textPrimary,
              fontFamily: textFamily,
            ),
          ),
          Text(
            subtitle,
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontSize: 11,
              fontFamily: textFamily,
            ),
          ),
        ],
      ),
    );
  }
}
class _DemandChart extends StatelessWidget {
  final List<Map<String, dynamic>> points;

  const _DemandChart({required this.points});

  @override
  Widget build(BuildContext context) {
    final textFamily =
        Theme.of(context).textTheme.bodyMedium?.fontFamily ?? 'Poppins';

    if (points.isEmpty) {
      return Center(
        child: Text(
          'Prediksi harian belum tersedia.',
          style: TextStyle(
            color: AppTheme.textSecondary,
            fontSize: 12,
            fontFamily: textFamily,
          ),
        ),
      );
    }

    final values = points.map((point) {
      final value = point['predicted_qty'];
      return value is num ? value.toDouble() : 0.0;
    }).toList();
    final maxValue = values.fold<double>(0, (max, value) => value > max ? value : max);

    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: values.asMap().entries.map((entry) {
        final value = entry.value;
        final height = maxValue == 0 ? 0.0 : (value / maxValue) * 150;

        return Expanded(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              Text(
                '${value.round()}',
                style: TextStyle(
                  fontSize: 10,
                  color: AppTheme.textSecondary,
                  fontFamily: textFamily,
                ),
              ),
              const SizedBox(height: 5),
              Container(
                height: height,
                margin: const EdgeInsets.symmetric(horizontal: 5),
                decoration: BoxDecoration(
                  color: AppTheme.primary.withValues(alpha: 0.75),
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(7)),
                ),
              ),
              const SizedBox(height: 7),
              Text(
                'D${entry.key + 1}',
                style: TextStyle(
                  fontSize: 10,
                  color: AppTheme.textSecondary,
                  fontFamily: textFamily,
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }
}
