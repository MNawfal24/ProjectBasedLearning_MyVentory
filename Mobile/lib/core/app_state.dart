import 'package:myventory/core/controllers/auth_controller.dart';
import 'package:myventory/core/network/api_client.dart';
import 'package:myventory/features/auth/data/auth_remote_datasource.dart';
import 'package:myventory/features/auth/domain/auth_repository.dart';

/// Instance tunggal pengelola autentikasi di seluruh aplikasi.
final authController = AuthController(
  AuthRepositoryImpl(AuthRemoteDataSource(ApiClient().dio)),
);
