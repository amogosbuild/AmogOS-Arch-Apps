// Onboarding previews desktop appearance and changes accounts only after the user completes setup.
import 'dart:convert';
import 'dart:io';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'account.dart';

class Onboarding extends StatefulWidget {
  const Onboarding({super.key});

  @override
  State<Onboarding> createState() => _OnboardingState();
}

class _OnboardingState extends State<Onboarding> {
  final name = TextEditingController();
  final username = TextEditingController();
  final password = TextEditingController();
  final confirmation = TextEditingController();
  bool dark = true, largerText = false, contrast = false, autoLogin = false;
  bool busy = false, completed = false;
  String? error;
  int step = 0;

  @override
  void dispose() {
    for (final field in [name, username, password, confirmation]) {
      field.dispose();
    }
    super.dispose();
  }

  Future<void> next() async {
    if (step == 1) {
      final validation = AccountFields.validate(name, username, password, confirmation);
      if (validation != null) {
        setState(() => error = validation);
        return;
      }
    }
    if (step < 2) {
      setState(() { step++; error = null; });
      return;
    }
    setState(() { busy = true; error = null; });
    try {
      final process = await Process.start('pkexec',
          ['/usr/lib/amogos-arch-onboarding/finish']);
      process.stdin.writeln(jsonEncode({
        'name': name.text.trim(), 'username': username.text,
        'password': password.text, 'theme': dark ? 'dark' : 'light',
        'autoLogin': autoLogin, 'largerText': largerText, 'highContrast': contrast,
      }));
      await process.stdin.close();
      final status = await Future.wait<Object>([
        process.exitCode, process.stdout.transform(utf8.decoder).join(),
        process.stderr.drain<void>().then<Object>((_) => ''),
      ]);
      if (status[0] != 0) {
        throw StateError((status[1] as String).trim().isEmpty
            ? 'Setup could not finish. Try again.' : (status[1] as String).trim());
      }
      password.clear();
      confirmation.clear();
      if (mounted) setState(() => completed = true);
    } catch (exception) {
      if (mounted) setState(() {
        error = exception.toString().replaceFirst('Bad state: ', '');
        busy = false;
      });
    }
  }

  Future<void> accessibility(BuildContext context) async {
    await showDialog<void>(context: context, builder: (context) =>
      StatefulBuilder(builder: (context, redraw) => AlertDialog(
        title: const Text('Accessibility'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          SwitchListTile(title: const Text('Larger text'), value: largerText,
            onChanged: (value) {
              setState(() => largerText = value);
              redraw(() {});
            }),
          SwitchListTile(title: const Text('High contrast'), value: contrast,
            onChanged: (value) {
              setState(() => contrast = value);
              redraw(() {});
            }),
        ]),
        actions: [TextButton(onPressed: () => Navigator.pop(context),
            child: const Text('Done'))],
      )),
    );
  }

  Widget page(BuildContext context) {
    switch (step) {
      case 0:
        return Wrap(spacing: 12, runSpacing: 12, children: [
          ChoiceChip(label: const Text('Light'), avatar: const Icon(Icons.light_mode),
            selected: !dark, onSelected: (_) => setState(() => dark = false)),
          ChoiceChip(label: const Text('Dark'), avatar: const Icon(Icons.dark_mode),
            selected: dark, onSelected: (_) => setState(() => dark = true)),
        ]);
      case 1:
        return AccountFields(name: name, username: username, password: password,
          confirmation: confirmation, autoLogin: autoLogin,
          onAutoLogin: (value) => setState(() => autoLogin = value));
      default:
        return const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          ListTile(leading: Icon(Icons.storefront_outlined),
            title: Text('AmogOS Arch App Store'),
            subtitle: Text('Find apps, manage system updates, or enable the AUR in Settings.')),
          ListTile(leading: Icon(Icons.sports_esports_outlined),
            title: Text('Steam and Steam Big Picture'),
            subtitle: Text('Open Steam from the desktop or launch Big Picture for a controller.')),
          ListTile(leading: Icon(Icons.tune_outlined),
            title: Text('Your desktop'),
            subtitle: Text('Change the theme, wallpaper, and shortcuts from desktop settings.')),
        ]);
    }
  }

  @override
  Widget build(BuildContext context) => MaterialApp(
    debugShowCheckedModeBanner: false,
    theme: ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xff1798bd),
        brightness: dark ? Brightness.dark : Brightness.light),
      useMaterial3: true,
    ),
    builder: (context, child) => MediaQuery(
      data: MediaQuery.of(context).copyWith(
        textScaler: largerText ? const TextScaler.linear(1.24) : MediaQuery.textScalerOf(context),
      ),
      child: child!,
    ),
    home: Builder(builder: (context) {
      final colors = Theme.of(context).colorScheme;
      final wallpaper = dark
          ? '/usr/share/wallpapers/AmogOSArch/2.png'
          : '/usr/share/wallpapers/AmogOSArch/4.png';
      return Scaffold(
        body: Stack(fit: StackFit.expand, children: [
          Image.file(File(wallpaper), fit: BoxFit.cover, excludeFromSemantics: true,
            errorBuilder: (_, _, _) => ColoredBox(color: colors.primaryContainer)),
          BackdropFilter(filter: ImageFilter.blur(sigmaX: 27, sigmaY: 27),
            child: ColoredBox(color: colors.surface.withValues(alpha: .28))),
          SafeArea(child: Center(child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 650),
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Flexible(child: Material(
                  color: colors.surface.withValues(alpha: contrast ? 1 : .86),
                  borderRadius: BorderRadius.circular(30),
                  elevation: 8, clipBehavior: Clip.antiAlias,
                  child: ListView(shrinkWrap: true,
                    padding: const EdgeInsets.all(28), children: [
                      Text(['Choose your appearance', 'Create your account', 'Explore AmogOS Arch'][step],
                        style: Theme.of(context).textTheme.headlineMedium),
                      const SizedBox(height: 14),
                      page(context),
                      if (error != null) ...[
                        const SizedBox(height: 12),
                        Semantics(liveRegion: true,
                          child: Text(error!, style: TextStyle(color: colors.error))),
                      ],
                    ],
                  ),
                )),
                const SizedBox(height: 18),
                Material(
                  color: colors.surface.withValues(alpha: contrast ? 1 : .8),
                  borderRadius: BorderRadius.circular(22),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: Row(children: [
                      IconButton(tooltip: 'Accessibility', icon: const Icon(Icons.accessibility_new),
                        onPressed: () => accessibility(context)),
                      const Spacer(),
                      TextButton(onPressed: step == 0 || busy ? null : () => setState(() {
                          step--; error = null;
                        }), child: const Text('Previous')),
                      const SizedBox(width: 8),
                      FilledButton(onPressed: busy ? null : next,
                        child: Text(completed ? 'Opening desktop…' : busy ? 'Setting up…' : step == 2 ? 'Finish' : 'Next')),
                    ]),
                  ),
                ),
              ]),
            ),
          ))),
        ]),
      );
    }),
  );
}
