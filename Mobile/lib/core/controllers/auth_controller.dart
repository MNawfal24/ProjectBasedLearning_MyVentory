import 'package:flutter/foundation.dart';

import 'package:myventory/features/auth/domain/auth_repository.dart';

/// Pengelola status autentikasi yang diakses oleh seluruh aplikasi.
class AuthController extends ChangeNotifier {
  final AuthRepository repository;

  AuthController(this.repository);

  bool _initialized = false;
  bool get initialized => _initialized;

  bool get isAuthenticated => repository.isAuthenticated;

  String? get token => repository.token;

  Map<String, dynamic>? get user => repository.user;

  bool get loading => repository.loading;
  String? get error => repository.error;

  /// Mulai aplikasi: baca token dari penyimpanan aman dan muat profil.
  Future<void> initialize() async {
    if (_initialized) return;
    _initialized = true;

    try {
      await repository.me();
    } catch (_) {
      // Token tersimpan tidak valid (mis. sudah kadaluarsa), buang dan arahkan ke login.
      await repository.logout();
    }
    notifyListeners();
  }

  Future<bool> login(String email, String password) async {
    final ok = await repository.login(email, password);
    notifyListeners();
    return ok;
  }

  Future<void> logout() async {
    await repository.logout();
    notifyListeners();
  }
}
