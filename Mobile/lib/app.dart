import 'package:flutter/material.dart';

import 'package:myventory/core/app_state.dart';
import 'data/mock_data.dart';
import 'pages/auth/login_page.dart';
import 'pages/dashboard/dashboard_page.dart';
import 'pages/products/products_page.dart';
import 'pages/predictions/prediction_page.dart';
import 'pages/profile/profile_page.dart';
import 'widgets/app_theme.dart';
import 'widgets/bottom_nav_bar.dart';

class MyventoryApp extends StatelessWidget {
  const MyventoryApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Myventory',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: const AuthGate(),
    );
  }
}

/// Gerbang autentikasi: halaman masuk ketika belum terautentikasi, dan
/// halaman utama aplikasi setelah masuk.
class AuthGate extends StatefulWidget {
  const AuthGate({super.key});

  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  @override
  void initState() {
    super.initState();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: authController,
      builder: (context, _) {
        if (!authController.initialized) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        if (!authController.isAuthenticated) {
          return LoginPage(
            auth: authController,
            onLoginSuccess: () => setState(() {}),
          );
        }

        return AppShell(store: InventoryStore());
      },
    );
  }
}

class AppShell extends StatefulWidget {
  final InventoryStore store;

  const AppShell({
    super.key,
    required this.store,
  });

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int currentIndex = 0;

  @override
  void initState() {
    super.initState();
    widget.store.load();
  }

  Future<void> _handleLogout() async {
    await authController.logout();
  }

  @override
  Widget build(BuildContext context) {
    final pages = [
      DashboardPage(
        store: widget.store,
        onOpenProducts: () {
          setState(() {
            currentIndex = 1;
          });
        },
      ),
      ProductsPage(store: widget.store),
      PredictionPage(store: widget.store),
      ProfilePage(
        store: widget.store,
        auth: authController,
        onLogout: _handleLogout,
      ),
    ];

    return Scaffold(
      body: IndexedStack(
        index: currentIndex,
        children: pages,
      ),
      bottomNavigationBar: AppBottomNavBar(
        currentIndex: currentIndex,
        onChanged: (index) {
          setState(() {
            currentIndex = index;
          });
        },
      ),
    );
  }
}
