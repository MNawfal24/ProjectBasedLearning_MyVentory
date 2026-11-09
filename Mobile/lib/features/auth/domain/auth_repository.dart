import 'package:myventory/core/network/api_client.dart';
import 'package:myventory/core/storage/token_storage.dart';

import '../data/auth_remote_datasource.dart';

/// Kontrak repositori autentikasi.
abstract class AuthRepository {
  Future<bool> login(String email, String password);
  Future<bool> register(String name, String email, String password);
  Future<void> logout();
  Future<Map<String, dynamic>?> me();
  bool get isAuthenticated;
  String? get token;
  Map<String, dynamic>? get user;
  bool get loading;
  String? get error;
}

/// Implementasi repositori autentikasi berbasis Laravel Sanctum.
class AuthRepositoryImpl implements AuthRepository {
  final AuthRemoteDataSource _remote;

  AuthRepositoryImpl(this._remote);

  String? _token;
  Map<String, dynamic>? _user;
  bool _loading = false;
  String? _error;

  @override
  bool get isAuthenticated => (_token ?? '').isNotEmpty;

  @override
  String? get token => _token;

  @override
  Map<String, dynamic>? get user => _user;

  @override
  bool get loading => _loading;
  @override
  String? get error => _error;

  @override
  Future<bool> login(String email, String password) async {
    _loading = true;
    _error = null;
    try {
      final data = await _remote.login(email: email, password: password);
      _token = data['token'] as String?;
      _user = data['user'] as Map<String, dynamic>?;
      if (_token != null && _token!.isNotEmpty) {
        await TokenStorage.write(_token!);
      }
      return true;
    } catch (e) {
      _error = ApiClient.errorFrom(e).message;
      return false;
    } finally {
      _loading = false;
    }
  }

  @override
  Future<bool> register(String name, String email, String password) async {
    _loading = true;
    _error = null;
    try {
      final data = await _remote.register(
        name: name,
        email: email,
        password: password,
      );
      _token = data['token'] as String?;
      _user = data['user'] as Map<String, dynamic>?;
      if (_token != null && _token!.isNotEmpty) {
        await TokenStorage.write(_token!);
      }
      return true;
    } catch (e) {
      _error = ApiClient.errorFrom(e).message;
      return false;
    } finally {
      _loading = false;
    }
  }

  @override
  Future<void> logout() async {
    try {
      await _remote.logout();
    } catch (_) {
      // Terjadi kesalahan saat memanggil server, tetap hapus token lokal.
    }
    await TokenStorage.clear();
    _token = null;
    _user = null;
  }

  @override
  Future<Map<String, dynamic>?> me() async {
    try {
      _user = await _remote.me();
      return _user;
    } catch (e) {
      _error = ApiClient.errorFrom(e).message;
      rethrow;
    }
  }
}
