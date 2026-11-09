/// Penyimpanan token autentikasi yang dienkripsi secara native.
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class TokenStorage {
  static const _key = 'myventory_auth_token';
  static final FlutterSecureStorage _storage = const FlutterSecureStorage();

  /// Simpan token JWT ke keystore/keychain native.
  static Future<void> write(String token) async {
    await _storage.write(key: _key, value: token);
  }

  /// Baca token yang disimpan. Mengembalikan null jika belum ada.
  static Future<String?> read() async => await _storage.read(key: _key);

  /// Hapus token (logout).
  static Future<void> clear() async => await _storage.delete(key: _key);
}
