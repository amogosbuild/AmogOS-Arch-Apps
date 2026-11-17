// The boot character sits behind a reduced-motion-aware shimmer greeting.
import 'package:flutter/material.dart';

class WelcomePage extends StatefulWidget {
  const WelcomePage({super.key});

  @override
  State<WelcomePage> createState() => _WelcomePageState();
}

class _WelcomePageState extends State<WelcomePage>
    with SingleTickerProviderStateMixin {
  late final AnimationController sweep = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 3250),
  );

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (MediaQuery.disableAnimationsOf(context)) {
      sweep.stop();
    } else if (!sweep.isAnimating) {
      sweep.repeat();
    }
  }

  @override
  void dispose() {
    sweep.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    final greeting = Text(
      'Ready to install AmogOS btw',
      textAlign: TextAlign.center,
      style: theme.textTheme.displaySmall,
    );

    return LayoutBuilder(
      builder: (context, box) => SingleChildScrollView(
        child: SizedBox(
          width: box.maxWidth,
          height: box.maxHeight.clamp(270.0, 620.0).toDouble(),
          child: Stack(
            fit: StackFit.expand,
            children: [
              DecoratedBox(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(30),
                  gradient: RadialGradient(
                    colors: [
                      colors.primary.withValues(alpha: .17),
                      colors.surface,
                    ],
                  ),
                ),
              ),
              Positioned.fill(
                child: IgnorePointer(
                  child: Opacity(
                    opacity: .27,
                    child: Image.asset(
                      'assets/images/boot-character.png',
                      fit: BoxFit.contain,
                      alignment: Alignment.center,
                    ),
                  ),
                ),
              ),
              Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: SingleChildScrollView(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          'AmogOS 2 Pro (Arch)',
                          style: theme.textTheme.titleLarge,
                        ),
                        const SizedBox(height: 20),
                        if (MediaQuery.disableAnimationsOf(context))
                          greeting
                        else
                          AnimatedBuilder(
                            animation: sweep,
                            child: greeting,
                            builder: (context, child) {
                              final shift = sweep.value * 4 - 2;
                              return ShaderMask(
                                blendMode: BlendMode.srcIn,
                                shaderCallback: (rect) => LinearGradient(
                                  begin: Alignment(shift - .7, 0),
                                  end: Alignment(shift + .7, 0),
                                  colors: [
                                    colors.onSurface.withValues(alpha: .72),
                                    theme.brightness == Brightness.dark
                                        ? Colors.white
                                        : colors.primary,
                                    colors.onSurface.withValues(alpha: .72),
                                  ],
                                ).createShader(rect),
                                child: child,
                              );
                            },
                          ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
