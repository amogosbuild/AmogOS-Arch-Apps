// The milestone list distinguishes active, completed and skipped system updates.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:amogos_installer/core/controllers/install_controller.dart';
import 'package:amogos_installer/core/models/install_models.dart';
import 'package:amogos_installer/features/setup/pages/install_page.dart';

void main() {
  for (final skipped in [false, true]) {
    testWidgets(
      'updates preserve completion and skipped state at boot setup $skipped',
      (tester) async {
        tester.view.devicePixelRatio = 1;
        tester.view.physicalSize = const Size(1280, 820);
        addTearDown(tester.view.resetDevicePixelRatio);
        addTearDown(tester.view.resetPhysicalSize);
        final controller = InstallController(preview: true)..step = 6;
        final update = InstallEvent.fromJson({
          'stage': 'updates',
          'progress': .83,
          'message': skipped
              ? 'Using offline packages'
              : 'Arch packages are up to date',
          'skipped': skipped,
        });
        controller.events.add(update);
        controller.event = const InstallEvent(
          'bootloader',
          .88,
          'Creating your boot menu',
        );
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: InstallPage(controller: controller, musicOpen: false),
            ),
          ),
        );
        await tester.pump();
        final row = find
            .ancestor(
              of: find.text(
                skipped ? 'System updates (skipped)' : 'System updates',
              ),
              matching: find.byType(Row),
            )
            .first;
        expect(
          find.descendant(
            of: row,
            matching: find.byIcon(
              skipped
                  ? Icons.remove_circle_outline_rounded
                  : Icons.check_circle_rounded,
            ),
          ),
          findsOneWidget,
        );
        expect(find.text('Your boot menu'), findsOneWidget);
        expect(tester.takeException(), isNull);
        await tester.pumpWidget(const SizedBox());
        controller.dispose();
      },
    );
  }

  testWidgets('system updates highlight while the backend runs them', (
    tester,
  ) async {
    tester.view.devicePixelRatio = 1;
    tester.view.physicalSize = const Size(1280, 820);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.view.resetPhysicalSize);
    final controller = InstallController(preview: true)
      ..step = 6
      ..event = const InstallEvent('updates', .72, 'Updating Arch packages');
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: InstallPage(controller: controller, musicOpen: false),
        ),
      ),
    );
    await tester.pump();
    final row = find
        .ancestor(of: find.text('System updates'), matching: find.byType(Row))
        .first;
    expect(
      find.descendant(
        of: row,
        matching: find.byType(CircularProgressIndicator),
      ),
      findsOneWidget,
    );
    expect(
      tester.widget<Text>(find.text('System updates')).style!.fontWeight,
      FontWeight.w800,
    );
    await tester.pumpWidget(const SizedBox());
    controller.dispose();
  });
}
