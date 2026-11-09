import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:myventory/app.dart';
import 'package:myventory/injection_container.dart';

void main() {
  testWidgets('login is required and profile logout returns to login', (
    WidgetTester tester,
  ) async {
    sl.init();
    await tester.pumpWidget(const MyventoryApp());

    expect(find.widgetWithText(FilledButton, 'Masuk'), findsOneWidget);
    expect(find.text('Dashboard'), findsNothing);

    // Buka halaman Login dari LandingPage
    await tester.tap(find.widgetWithText(FilledButton, 'Masuk'));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byType(TextFormField).at(0),
      'admin@myventory.com',
    );
    await tester.enterText(find.byType(TextFormField).at(1), 'admin123');
    await tester.tap(find.widgetWithText(FilledButton, 'Masuk'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 700));
    await tester.pumpAndSettle();

    expect(find.text('Dashboard'), findsOneWidget);

    await tester.tap(find.text('Profile').last);
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(find.text('Logout'), 300);
    await tester.tap(find.text('Logout').first);
    await tester.pumpAndSettle();

    expect(find.text('Are you sure you want to logout?'), findsOneWidget);
    await tester.tap(find.text('Logout').last);
    await tester.pumpAndSettle();

    expect(find.widgetWithText(FilledButton, 'Masuk'), findsOneWidget);
    expect(find.text('Dashboard'), findsNothing);
  });
}
