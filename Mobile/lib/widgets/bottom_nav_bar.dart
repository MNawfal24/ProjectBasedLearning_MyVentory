import 'package:flutter/material.dart';

import 'app_theme.dart';

class AppBottomNavBar extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onChanged;

  const AppBottomNavBar({
    super.key,
    required this.currentIndex,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.only(bottom: 6),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 12,
            offset: const Offset(0, -3),
          ),
        ],
      ),
      child: NavigationBar(
        selectedIndex: currentIndex,
        onDestinationSelected: onChanged,
        backgroundColor: Colors.white,
        indicatorColor: const Color(0xFFE8EEFF),
        surfaceTintColor: AppTheme.primary,
        shadowColor: Colors.transparent,
        elevation: 0,
        labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        destinations: [
          NavigationDestination(
            icon: const Icon(Icons.dashboard_outlined, color: Color(0xFF64748B)),
            selectedIcon: const Icon(Icons.dashboard, color: AppTheme.primary),
            label: 'Dashboard',
          ),
          NavigationDestination(
            icon: const Icon(Icons.inventory_2_outlined, color: Color(0xFF64748B)),
            selectedIcon: const Icon(Icons.inventory_2, color: AppTheme.primary),
            label: 'Products',
          ),
          NavigationDestination(
            icon: const Icon(Icons.insights_outlined, color: Color(0xFF64748B)),
            selectedIcon: const Icon(Icons.insights, color: AppTheme.primary),
            label: 'Prediction',
          ),
          NavigationDestination(
            icon: const Icon(Icons.person_outline, color: Color(0xFF64748B)),
            selectedIcon: const Icon(Icons.person, color: AppTheme.primary),
            label: 'Profile',
          ),
        ],
      ),
    );
  }
}