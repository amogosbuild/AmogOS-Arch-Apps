// Offer regular removal or Pacman's recursive removal with configuration cleanup.
import 'package:flutter/material.dart';

class UninstallOptions extends StatelessWidget {
  const UninstallOptions({
    super.key,
    required this.enabled,
    required this.onSelected,
  });

  final bool enabled;
  final ValueChanged<bool> onSelected;

  @override
  Widget build(BuildContext context) {
    final color = enabled
        ? Theme.of(context).colorScheme.primary
        : Theme.of(context).colorScheme.onSurface.withValues(alpha: .38);
    return PopupMenuButton<bool>(
      enabled: enabled,
      tooltip: 'Uninstall options',
      onSelected: onSelected,
      constraints: const BoxConstraints(maxWidth: 340),
      itemBuilder: (context) => [
        const PopupMenuItem(value: false, child: Text('Uninstall')),
        const PopupMenuItem(
          value: true,
          child: Padding(
            padding: EdgeInsets.symmetric(vertical: 6),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('Full uninstall (-Rns)'),
                SizedBox(height: 4),
                Text(
                  'Also remove unused dependencies and package configuration.',
                  style: TextStyle(fontSize: 12),
                ),
              ],
            ),
          ),
        ),
      ],
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.delete_outline_rounded, size: 18, color: color),
            const SizedBox(width: 8),
            Text('Remove', style: TextStyle(color: color)),
            Icon(Icons.arrow_drop_down_rounded, color: color),
          ],
        ),
      ),
    );
  }
}
