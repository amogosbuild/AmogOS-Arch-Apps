// Location, keyboard, and account pages collect validated configuration without logging passwords.
import 'package:flutter/material.dart';

import '../../../core/controllers/install_controller.dart';
import '../widgets/setup_widgets.dart';

class LocationPage extends StatelessWidget {
  const LocationPage({super.key, required this.controller});
  final InstallController controller;
  @override
  Widget build(BuildContext context) {
    final c = controller;
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const PageIntro(
            eyebrow: 'A world of possibilities',
            title: 'Where do you call home?',
            description:
                'Let’s get your language and local time feeling familiar.',
          ),
          SurfaceCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const InfoLine(
                  icon: Icons.public_rounded,
                  title: 'Your corner of the world',
                  detail: 'Your time zone keeps the clock, calendar, and daylight saving in sync.',
                ),
                const SizedBox(height: 20),
                DropdownButtonFormField<String>(
                  initialValue: c.timezone,
                  isExpanded: true,
                  decoration: const InputDecoration(
                    labelText: 'Time zone',
                    prefixIcon: Icon(Icons.schedule_rounded),
                  ),
                  items: [
                    for (final z in [
                      'Europe/London',
                      'Europe/Paris',
                      'Europe/Berlin',
                      'Europe/Madrid',
                      'Europe/Rome',
                      'Europe/Warsaw',
                      'Europe/Kyiv',
                      'Europe/Istanbul',
                      'America/New_York',
                      'America/Chicago',
                      'America/Denver',
                      'America/Los_Angeles',
                      'America/Toronto',
                      'America/Sao_Paulo',
                      'Asia/Kolkata',
                      'Asia/Tokyo',
                      'Asia/Shanghai',
                      'Asia/Singapore',
                      'Asia/Dubai',
                      'Australia/Sydney',
                      'Pacific/Auckland',
                      'Africa/Johannesburg',
                      'Africa/Cairo',
                      'UTC',
                    ])
                      DropdownMenuItem(
                        value: z,
                        child: Text(
                          z.replaceAll('_', ' '),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                  ],
                  onChanged: (v) => c.change(() => c.timezone = v!),
                ),
                const SizedBox(height: 20),
                DropdownButtonFormField<String>(
                  initialValue: c.locale,
                  isExpanded: true,
                  decoration: const InputDecoration(
                    labelText: 'System language',
                    prefixIcon: Icon(Icons.translate_rounded),
                  ),
                  items: [
                    for (final l in [
                      ('en_GB.UTF-8', 'English (United Kingdom)'),
                      ('en_US.UTF-8', 'English (United States)'),
                      ('de_DE.UTF-8', 'Deutsch'),
                      ('fr_FR.UTF-8', 'Français'),
                      ('es_ES.UTF-8', 'Español'),
                      ('pt_BR.UTF-8', 'Português (Brasil)'),
                      ('pl_PL.UTF-8', 'Polski'),
                      ('ja_JP.UTF-8', '日本語'),
                    ])
                      DropdownMenuItem(
                        value: l.$1,
                        child: Text(
                          l.$2,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                  ],
                  onChanged: (v) => c.change(() => c.locale = v!),
                ),
                const SizedBox(height: 16),
                Text(
                  'These settings apply to your installed system. You can change them later.',
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class KeyboardPage extends StatelessWidget {
  const KeyboardPage({super.key, required this.controller});
  final InstallController controller;
  @override
  Widget build(BuildContext context) => SingleChildScrollView(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const PageIntro(
          eyebrow: 'Just your type',
          title: 'Make yourself understood.',
          description: 'Choose the layout that matches your keyboard, then give it a little test.',
        ),
        SurfaceCard(
          child: Column(
            children: [
              DropdownButtonFormField<String>(
                initialValue: controller.keyboard,
                isExpanded: true,
                decoration: const InputDecoration(
                  labelText: 'Keyboard layout',
                  prefixIcon: Icon(Icons.keyboard_outlined),
                ),
                items: [
                  for (final l in [
                    ('gb', 'English (UK)'),
                    ('us', 'English (US)'),
                    ('de', 'German'),
                    ('fr', 'French'),
                    ('es', 'Spanish'),
                    ('it', 'Italian'),
                    ('br', 'Portuguese (Brazil)'),
                    ('pt', 'Portuguese'),
                    ('pl', 'Polish'),
                    ('jp', 'Japanese'),
                    ('in', 'Indian'),
                    ('tr', 'Turkish'),
                  ])
                    DropdownMenuItem(
                      value: l.$1,
                      child: Text(
                        l.$2,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                ],
                onChanged: (v) =>
                    controller.change(() => controller.keyboard = v!),
              ),
              const SizedBox(height: 26),
              for (final row in [
                'Q W E R T Y U I O P',
                'A S D F G H J K L',
                'Z X C V B N M',
              ])
                Padding(
                  padding: const EdgeInsets.only(bottom: 7),
                  child: FittedBox(
                    fit: BoxFit.scaleDown,
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        for (final letter in row.split(' '))
                          Container(
                            width: 42,
                            height: 40,
                            margin: const EdgeInsets.symmetric(horizontal: 3),
                            alignment: Alignment.center,
                            decoration: BoxDecoration(
                              color: Theme.of(context)
                                  .colorScheme
                                  .surfaceContainerLow,
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(
                                color: Theme.of(context)
                                    .colorScheme
                                    .outlineVariant,
                              ),
                            ),
                            child: Text(
                              letter,
                              style: const TextStyle(
                                fontWeight: FontWeight.w700,
                                fontSize: 12,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 22),
              const TextField(
                decoration: InputDecoration(
                  labelText: 'Try your keyboard here',
                  hintText: 'Hello, AmogOS 2 Pro (Arch)! @ # £ €',
                  prefixIcon: Icon(Icons.edit_outlined),
                ),
              ),
              const SizedBox(height: 10),
              Text(
                'The test field uses your current live-session layout. The selected layout is saved for the installed system.',
                style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                  fontSize: 11,
                ),
              ),
            ],
          ),
        ),
      ],
    ),
  );
}

class FirstBootPage extends StatelessWidget {
  const FirstBootPage({super.key});

  @override
  Widget build(BuildContext context) => SingleChildScrollView(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Set up your desktop after restarting',
            style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 16),
        const Text('Choose a light or dark theme, create your account, and explore your new desktop.'),
        const SizedBox(height: 12),
        const Text('You can turn on automatic login during first-boot setup.'),
      ],
    ),
  );
}
