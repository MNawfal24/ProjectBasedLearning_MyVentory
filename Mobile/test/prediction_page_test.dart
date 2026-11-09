import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:myventory/app.dart';
import 'package:myventory/data/mock_data.dart';
import 'package:myventory/features/product/domain/entities/product.dart';
import 'package:myventory/injection_container.dart';
import 'package:myventory/pages/predictions/prediction_page.dart';

class FakeInventoryStore extends InventoryStore {
  List<Product> _fakeProducts = [];
  bool _fakeLoading = false;

  @override
  List<Product> get products => _fakeProducts;

  @override
  bool get loading => _fakeLoading;

  @override
  int get totalProducts => _fakeProducts.length;

  @override
  int get totalLowStock => _fakeProducts.where((p) => p.isLowStock).length;

  @override
  int get totalStock => _fakeProducts.fold(0, (sum, p) => sum + p.stock);

  @override
  List<Product> get lowStockProducts => _fakeProducts.where((p) => p.isLowStock).toList();

  void setProducts(List<Product> newProducts) {
    _fakeProducts = List.from(newProducts);
    notifyListeners();
  }

  void setLoading(bool isLoading) {
    _fakeLoading = isLoading;
    notifyListeners();
  }

  @override
  int predictedDemand(Product product) => 15;

  @override
  int recommendedRestock(Product product) => 10;

  @override
  Future<void> load({String? outletId}) async {}

  @override
  Future<Map<String, dynamic>> fetchDashboardSummary({
    int days = 30,
    String? outletId,
  }) async {
    return {
      'kpis': {
        'revenue': {'value': 1000000.0}
      },
      'low_stock': [],
    };
  }
}

void main() {
  setUpAll(() {
    sl.init();
  });

  final sampleProduct1 = Product(
    id: 'prod-1',
    name: 'Kopi Arabika',
    category: 'Coffee',
    stock: 25,
    minStock: 5,
    unit: 'Kg',
    buyPrice: 50000,
    sellPrice: 75000,
  );

  final sampleProduct2 = Product(
    id: 'prod-2',
    name: 'Susu UHT',
    category: 'Dairy',
    stock: 42,
    minStock: 4,
    unit: 'Liter',
    buyPrice: 15000,
    sellPrice: 20000,
  );

  group('PredictionPage Runtime & State Tests', () {
    testWidgets('1. Kondisi data sedang dimuat: tampilkan loading indicator', (tester) async {
      final store = FakeInventoryStore();
      store.setLoading(true);

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PredictionPage(store: store),
          ),
        ),
      );

      // Loading indicator harus muncul
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Prediction'), findsNothing);
    });

    testWidgets('2. Kondisi produk kosong: tampilkan empty state yang informatif', (tester) async {
      final store = FakeInventoryStore();
      store.setLoading(false);
      store.setProducts([]);

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PredictionPage(store: store),
          ),
        ),
      );

      // Empty state harus muncul dan tidak melempar error
      expect(find.text('Belum Ada Produk'), findsOneWidget);
      expect(find.byType(CircularProgressIndicator), findsNothing);
    });

    testWidgets('3. Kondisi produk tersedia: tampilkan halaman prediksi dengan produk valid', (tester) async {
      final store = FakeInventoryStore();
      store.setProducts([sampleProduct1, sampleProduct2]);

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PredictionPage(store: store),
          ),
        ),
      );

      // Halaman prediksi dan nama produk harus muncul
      expect(find.text('Prediction'), findsOneWidget);
      expect(find.text('Kopi Arabika'), findsOneWidget);
      expect(find.text('25'), findsOneWidget); // Current stock
      expect(find.text('15'), findsOneWidget); // Predicted demand
    });

    testWidgets('4. Data produk selesai dimuat setelah PredictionPage diinisialisasi', (tester) async {
      final store = FakeInventoryStore();
      store.setLoading(true);
      store.setProducts([]);

      // Inisialisasi awal saat produk masih kosong / loading
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PredictionPage(store: store),
          ),
        ),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);

      // Simulasikan produk selesai dimuat asynchronous
      store.setLoading(false);
      store.setProducts([sampleProduct1, sampleProduct2]);
      await tester.pumpAndSettle();

      // UI harus reaktif memperbarui tampilan ke halaman prediksi
      expect(find.byType(CircularProgressIndicator), findsNothing);
      expect(find.text('Prediction'), findsOneWidget);
      expect(find.text('Kopi Arabika'), findsOneWidget);
    });

    testWidgets('5. Dropdown tetap valid setelah daftar produk di-refresh atau berubah', (tester) async {
      final store = FakeInventoryStore();
      store.setProducts([sampleProduct1, sampleProduct2]);

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PredictionPage(store: store),
          ),
        ),
      );

      // Pilih produk kedua dari dropdown
      await tester.tap(find.byType(DropdownButtonFormField<String>));
      await tester.pumpAndSettle();

      // Tap opsi Susu UHT
      await tester.tap(find.text('Susu UHT').last);
      await tester.pumpAndSettle();

      expect(find.text('42'), findsOneWidget); // Current stock Susu UHT

      // Refresh / perbarui data produk dari backend (misal stok bertambah)
      final updatedProduct2 = sampleProduct2.copyWith(stock: 88);
      store.setProducts([sampleProduct1, updatedProduct2]);
      await tester.pumpAndSettle();

      // Dropdown tetap valid dan menampilkan data terbaru tanpa crash/assertion error
      expect(find.text('88'), findsOneWidget);

      // Hapus produk yang sedang dipilih (fallback ke produk pertama)
      store.setProducts([sampleProduct1]);
      await tester.pumpAndSettle();

      // Harus fallback secara aman ke Kopi Arabika tanpa assertion error
      expect(find.text('Kopi Arabika'), findsOneWidget);
      expect(find.text('25'), findsOneWidget);
    });

    testWidgets('6. AppShell tidak crash saat pertama kali login dan masuk Dashboard', (tester) async {
      final store = FakeInventoryStore();
      store.setLoading(true);
      store.setProducts([]);

      // AppShell menggunakan IndexedStack yang menginisialisasi seluruh tab (Dashboard, Products, Prediction, Profile)
      await tester.pumpWidget(
        MaterialApp(
          home: AppShell(store: store),
        ),
      );
      await tester.pump();

      // Tidak boleh ada exception `Bad state: No element`
      expect(tester.takeException(), isNull);
      expect(find.byType(AppShell), findsOneWidget);
      expect(find.text('Dashboard'), findsOneWidget);
    });
  });
}
