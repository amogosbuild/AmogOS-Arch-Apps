// Direct AUR access is a per-user preference and starts disabled.
import 'package:flutter/material.dart';
import '../../core/controllers/store_controller.dart';

class SettingsPage extends StatelessWidget {
  const SettingsPage({super.key, required this.controller});

  final StoreController controller;

  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.all(16),
    children: [
      Text('Settings', style: Theme.of(context).textTheme.headlineMedium),
      const SizedBox(height: 16),
      SwitchListTile(
        title: const Text('Enable the Arch User Repository'),
        subtitle: const Text(
          'Browse community recipes and review the PKGBUILD before building with makepkg.',
        ),
        value: controller.aurEnabled,
        onChanged: controller.configureAur,
      ),
    ],
  );
}
