// Verify uninstall choices carry the reviewed mode and remain scoped to Arch packages.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:amogos_store/core/controllers/store_controller.dart';
import 'package:amogos_store/core/models/store_models.dart';
import 'package:amogos_store/core/services/store_service.dart';
import 'package:amogos_store/features/details/package_details.dart';

class RemovalService extends StoreService {
  RemovalService(this.source) : super(preview: true);
  final String source;
  Map<String, dynamic>? plan;
  String? appliedAction;
  Map<String, dynamic> get item => {
    'id': 'demo',
    'name': 'Demo',
    'source': source,
    'repo': source == 'flatpak' ? 'flathub' : 'extra',
    'installed': true,
  };

  @override
  Future<Map<String, dynamic>> request(
    String action, [
    Map<String, dynamic> body = const {},
  ]) async {
    if (action == 'details') return item;
    if (action == 'alternatives') {
      return {
        'items': [item],
      };
    }
    if (action == 'pacman-plan') {
      plan = body;
      return {
        'fullUninstall': body['fullUninstall'] == true,
        'token': 'removal-review',
        'changes': [
          {'id': 'demo', 'action': 'remove'},
          if (body['fullUninstall'] == true)
            {'id': 'unused-library', 'action': 'remove'},
        ],
        'note': 'Files in your home folder are kept.',
      };
    }
    return {};
  }

  @override
  Stream<Map<String, dynamic>> execute(
    String action,
    Map<String, dynamic> body,
  ) async* {
    appliedAction = action;
    yield {'done': true, 'message': 'Removed', 'progress': 1};
  }
}

void main() {
  for (final source in ['pacman', 'aur']) {
    for (final full in [false, true]) {
      testWidgets(
        '$source removal reviews full=$full and cancellation queues nothing',
        (tester) async {
          tester.view.physicalSize = const Size(360, 640);
          tester.view.devicePixelRatio = 1;
          addTearDown(tester.view.resetPhysicalSize);
          addTearDown(tester.view.resetDevicePixelRatio);
          final service = RemovalService(source);
          final controller = StoreController(service: service);
          await tester.pumpWidget(
            MaterialApp(
              home: Builder(
                builder: (context) => Scaffold(
                  body: TextButton(
                    onPressed: () => showPackage(
                      context,
                      controller,
                      StorePackage(service.item),
                    ),
                    child: const Text('Details'),
                  ),
                ),
              ),
            ),
          );
          await tester.tap(find.text('Details'));
          await tester.pumpAndSettle();
          await tester.ensureVisible(find.byTooltip('Uninstall options'));
          await tester.tap(find.byTooltip('Uninstall options'));
          await tester.pumpAndSettle();
          await tester.tap(
            find.text(full ? 'Full uninstall (-Rns)' : 'Uninstall'),
          );
          await tester.pumpAndSettle();
          expect(service.plan?['operation'], 'remove');
          expect(service.plan?['fullUninstall'] == true, full);
          expect(service.plan?['source'], 'pacman');
          expect(
            find.text(full ? 'Fully uninstall Demo?' : 'Remove Demo?'),
            findsOneWidget,
          );
          if (full) expect(find.text('unused-library'), findsOneWidget);
          await tester.tap(find.text('Cancel'));
          await tester.pumpAndSettle();
          expect(controller.queue, isEmpty);
          if (full) {
            await tester.tap(find.byTooltip('Uninstall options'));
            await tester.pumpAndSettle();
            await tester.tap(find.text('Full uninstall (-Rns)'));
            await tester.pumpAndSettle();
            expect(find.textContaining('Download:'), findsNothing);
            await tester.tap(find.text('Queue preview'));
            await tester.pumpAndSettle();
            final job = controller.queue.single;
            expect(job.request['fullUninstall'], isTrue);
            expect(job.source, 'pacman');
            expect(job.activity, 'Uninstalling');
            expect(job.status, JobStatus.completed);
            expect(service.appliedAction, 'pacman-apply');
            expect(service.plan?['fullUninstall'], isTrue);
          }
          expect(tester.takeException(), isNull);
          await tester.pumpWidget(const SizedBox());
          controller.dispose();
        },
      );
    }
  }

  testWidgets('Flatpak keeps its regular remove action', (tester) async {
    final service = RemovalService('flatpak');
    final controller = StoreController(service: service);
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PackageDetails(
            controller: controller,
            initial: StorePackage(service.item),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Remove'), findsOneWidget);
    expect(find.byTooltip('Uninstall options'), findsNothing);
    await tester.pumpWidget(const SizedBox());
    controller.dispose();
  });
}
