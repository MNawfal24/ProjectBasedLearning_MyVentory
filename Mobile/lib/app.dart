import 'package:flutter/material.dart';

import 'data/mock_data.dart';
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
      home: const AppShell(),
    );
  }
}

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  final InventoryStore store = InventoryStore();

  int currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    final pages = [
      DashboardPage(
        store: store,
        onOpenProducts: () {
          setState(() {
            currentIndex = 1;
          });
        },
      ),
      ProductsPage(store: store),
      PredictionPage(store: store),
      ProfilePage(store: store),
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