import 'package:flutter/material.dart';

import 'package:myventory/data/mock_data.dart';
import 'package:myventory/widgets/app_theme.dart';
import 'package:myventory/widgets/stat_card.dart';

class DashboardPage extends StatefulWidget {
  final InventoryStore store;
  final VoidCallback onOpenProducts;

  const DashboardPage({
    super.key,
    required this.store,
    required this.onOpenProducts,
  });

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  Map<String, dynamic>? _summary;
  bool _loadingSummary = false;

  String currency(double value) {
    return 'Rp ${value.toStringAsFixed(0)}';
  }

  double _todaySales() {
    if (_summary == null) return 0.0;
    final kpis = _summary!['kpis'];
    if (kpis == null) return 0.0;
    final revenue = kpis['revenue'];
    if (revenue == null) return 0.0;
    return (revenue is Map) ? (revenue['value'] ?? 0.0) : 0.0;
  }

  @override
  void initState() {
    super.initState();
    _loadSummary();
  }

  Future<void> _loadSummary() async {
    setState(() {
      _loadingSummary = true;
    });
    try {
      final summary = await widget.store.fetchDashboardSummary(days: 30);
      if (mounted) setState(() => _summary = summary);
    } catch (_) {
      // ignore
    } finally {
      if (mounted) setState(() => _loadingSummary = false);
    }
  }

  List<Widget> _buildLowStockWidgets() {
    if (widget.store.lowStockProducts.isEmpty) {
      return [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Text(
            'All products have sufficient stock.',
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontFamily:
                  Theme.of(context).textTheme.bodyMedium?.fontFamily ?? 'Poppins',
            ),
          ),
        ),
      ];
    }
    return widget.store.lowStockProducts.take(3).map((product) {
      return Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 13),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
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
            CircleAvatar(
              radius: 20,
              backgroundColor: AppTheme.primary.withValues(alpha: 0.08),
              child: const Icon(
                Icons.warning_amber_rounded,
                color: AppTheme.warning,
                size: 21,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    product.name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: AppTheme.textPrimary,
                      fontFamily:
                          Theme.of(context).textTheme.bodyMedium?.fontFamily ??
                          'Poppins',
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    'Stock ${product.stock} ${product.unit} • Min ${product.minStock}',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 12,
                      color: AppTheme.textSecondary,
                      fontFamily:
                          Theme.of(context).textTheme.bodyMedium?.fontFamily ??
                          'Poppins',
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            const Icon(
              Icons.chevron_right,
              color: AppTheme.textSecondary,
            ),
          ],
        ),
      );
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final textFamily =
        Theme.of(context).textTheme.bodyMedium?.fontFamily ?? 'Poppins';

    final headerChildren = <Widget>[
      Expanded(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Halo, Pengguna',
              style: TextStyle(
                color: AppTheme.textPrimary,
                fontSize: 28,
                fontWeight: FontWeight.w700,
                fontFamily: textFamily,
              ),
            ),
            const SizedBox(height: 5),
            Text(
              'Selamat mengelola inventaris Anda',
              style: TextStyle(
                color: AppTheme.textSecondary,
                fontFamily: textFamily,
              ),
            ),
          ],
        ),
      ),
      ...[_loadingSummary ? const Padding(
            padding: EdgeInsets.only(left: 12),
            child: SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
          ) : const SizedBox.shrink()],
    ];

    return AnimatedBuilder(
      animation: widget.store,
      builder: (context, _) {
        return Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [Color(0xFFEAF2FF), Color(0xFFF5F7FB)],
            ),
          ),
          child: SafeArea(
            child: RefreshIndicator(
              onRefresh: _loadSummary,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.fromLTRB(20, 18, 20, 110),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: headerChildren,
                    ),
                    const SizedBox(height: 18),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 18,
                        vertical: 16,
                      ),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [AppTheme.primary, const Color(0xFF3D69D3)],
                          begin: Alignment.centerLeft,
                          end: Alignment.centerRight,
                        ),
                        borderRadius: BorderRadius.circular(22),
                        boxShadow: [
                          BoxShadow(
                            color: AppTheme.primary.withValues(alpha: 0.24),
                            blurRadius: 18,
                            offset: const Offset(0, 8),
                          ),
                        ],
                      ),
                      child: Row(
                        children: [
                          Container(
                            width: 44,
                            height: 44,
                            decoration: BoxDecoration(
                              color: Colors.white.withValues(alpha: 0.18),
                              borderRadius: BorderRadius.circular(14),
                            ),
                            child: const Icon(
                              Icons.trending_up_rounded,
                              color: Colors.white,
                            ),
                          ),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Today sales',
                                  style: TextStyle(
                                    color: Colors.white.withValues(alpha: 0.8),
                                    fontSize: 12,
                                    fontFamily: textFamily,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  currency(_todaySales()),
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: 24,
                                    fontWeight: FontWeight.w700,
                                    fontFamily: textFamily,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 10,
                              vertical: 6,
                            ),
                            decoration: BoxDecoration(
                              color: Colors.white.withValues(alpha: 0.18),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              _summary == null ? '--' : '+0.0%',
                              style: TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w700,
                                fontFamily: textFamily,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 22),
                    GridView.count(
                      crossAxisCount: 2,
                      crossAxisSpacing: 12,
                      mainAxisSpacing: 12,
                      childAspectRatio: 1.08,
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      children: [
                        StatCard(
                          title: 'Products',
                          value: '${widget.store.totalProducts}',
                          subtitle: 'Total products',
                          icon: Icons.inventory_2_outlined,
                          color: AppTheme.primary,
                        ),
                        StatCard(
                          title: 'Low Stock',
                          value: '${widget.store.totalLowStock}',
                          subtitle: 'Need attention',
                          icon: Icons.warning_amber_rounded,
                          color: AppTheme.warning,
                        ),
                        StatCard(
                          title: 'Stock',
                          value: '${widget.store.totalStock}',
                          subtitle: 'Total quantity',
                          icon: Icons.layers_outlined,
                          color: AppTheme.secondary,
                        ),
                        StatCard(
                          title: 'Sales',
                          value: currency(_todaySales()),
                          subtitle: 'Today',
                          icon: Icons.payments_outlined,
                          color: AppTheme.primary,
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'Inventory Alert',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w700,
                            color: AppTheme.textPrimary,
                            fontFamily: textFamily,
                          ),
                        ),
                        TextButton(
                          onPressed: widget.onOpenProducts,
                          child: Text(
                            'View all',
                            style: TextStyle(
                              color: AppTheme.primary,
                              fontWeight: FontWeight.w600,
                              fontFamily: textFamily,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    ..._buildLowStockWidgets(),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
