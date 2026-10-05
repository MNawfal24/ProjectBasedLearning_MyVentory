import 'package:flutter_test/flutter_test.dart';

import 'package:inventoy/app.dart';

void main() {
  testWidgets('Myventory app loads correctly', (WidgetTester tester) async {
    await tester.pumpWidget(const MyventoryApp());

    expect(find.text('Dashboard'), findsOneWidget);
    expect(find.text('Products'), findsWidgets);
    expect(find.text('Prediction'), findsOneWidget);
    expect(find.text('Profile'), findsOneWidget);
    expect(find.text('Transactions'), findsNothing);
  });
}