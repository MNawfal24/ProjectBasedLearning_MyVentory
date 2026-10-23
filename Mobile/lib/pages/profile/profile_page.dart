import 'package:flutter/material.dart';

import '../../data/mock_data.dart';
import '../../widgets/app_theme.dart';

class ProfilePage extends StatelessWidget {
  final InventoryStore store;

  const ProfilePage({
    super.key,
    required this.store,
  });

  @override
  Widget build(BuildContext context) {
    final textFamily = Theme.of(context).textTheme.bodyMedium?.fontFamily ?? 'Poppins';

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
            children: [
              Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  'Profile',
                  style: TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.textPrimary,
                    fontFamily: textFamily,
                  ),
                ),
              ),
              const SizedBox(height: 22),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(24),
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
                  children: [
                    CircleAvatar(
                      radius: 42,
                      backgroundColor: AppTheme.primary.withValues(alpha: 0.12),
                      child: Icon(
                        Icons.store,
                        size: 38,
                        color: AppTheme.primary,
                      ),
                    ),
                    const SizedBox(height: 15),
                    Text(
                      'Kopi Senja Cafe',
                      style: TextStyle(
                        fontSize: 21,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.textPrimary,
                        fontFamily: textFamily,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      'Cafe & Coffee Shop',
                      style: TextStyle(
                        color: AppTheme.textSecondary,
                        fontFamily: textFamily,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),
              _MenuItem(
                icon: Icons.storefront_outlined,
                title: 'Store Information',
                subtitle: 'Manage your store profile',
                onTap: () {
                  _showInfoDialog(
                    context,
                    'Store Information',
                    'Kopi Senja Cafe\nMalang, Indonesia',
                  );
                },
              ),
              _MenuItem(
                icon: Icons.notifications_none,
                title: 'Notifications',
                subtitle: 'Manage notification preferences',
                onTap: () {
                  _showInfoDialog(
                    context,
                    'Notifications',
                    'Low stock notifications are enabled.',
                  );
                },
              ),
              _MenuItem(
                icon: Icons.settings_outlined,
                title: 'Settings',
                subtitle: 'Application settings',
                onTap: () {
                  _showInfoDialog(
                    context,
                    'Settings',
                    'Settings page will be connected later.',
                  );
                },
              ),
              _MenuItem(
                icon: Icons.info_outline,
                title: 'About Myventory',
                subtitle: 'Smart Inventory for UMKM',
                onTap: () {
                  _showInfoDialog(
                    context,
                    'About Myventory',
                    'Smart Inventory prototype for UMKM and cafe businesses.',
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showInfoDialog(BuildContext context, String title, String message) {
    showDialog(
      context: context,
      builder: (_) {
        return AlertDialog(
          title: Text(title),
          content: Text(message),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(context);
              },
              child: const Text('Close'),
            ),
          ],
        );
      },
    );
  }
}

class _MenuItem extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _MenuItem({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final textFamily = Theme.of(context).textTheme.bodyMedium?.fontFamily ?? 'Poppins';
    final primary = AppTheme.primary;

    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      child: ListTile(
        onTap: onTap,
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
        leading: Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: primary.withValues(alpha: 0.08),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(
            icon,
            color: primary,
          ),
        ),
        title: Text(
          title,
          style: TextStyle(
            fontWeight: FontWeight.w700,
            color: AppTheme.textPrimary,
            fontFamily: textFamily,
          ),
        ),
        subtitle: Text(
          subtitle,
          style: TextStyle(
            color: AppTheme.textSecondary,
            fontFamily: textFamily,
          ),
        ),
        trailing: Icon(
          Icons.chevron_right,
          color: AppTheme.textSecondary,
        ),
      ),
    );
  }
}