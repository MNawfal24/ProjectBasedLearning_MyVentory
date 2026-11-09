import 'package:flutter/material.dart';

import 'app.dart';
import 'core/app_state.dart';
import 'injection_container.dart';

void main() {
  sl.init();
  authController.initialize();
  runApp(const MyventoryApp());
}
