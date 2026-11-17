// Account inputs are validated before being passed to the first-boot helper.
import 'package:flutter/material.dart';

class AccountFields extends StatelessWidget {
  const AccountFields({
    super.key, required this.name, required this.username,
    required this.password, required this.confirmation,
    required this.autoLogin, required this.onAutoLogin,
  });

  final TextEditingController name, username, password, confirmation;
  final bool autoLogin;
  final ValueChanged<bool> onAutoLogin;

  static String? validate(TextEditingController name, TextEditingController username,
      TextEditingController password, TextEditingController confirmation) {
    if (name.text.trim().isEmpty || name.text.length > 80) return 'Enter your full name.';
    if (!RegExp(r'^[a-z_][a-z0-9_-]{0,30}$').hasMatch(username.text)) {
      return 'Use lowercase letters, digits, underscores, or hyphens in the username.';
    }
    if (password.text.length < 8 || password.text != confirmation.text) {
      return 'Enter matching passwords of at least eight characters.';
    }
    return null;
  }

  @override
  Widget build(BuildContext context) => AutofillGroup(
    child: Column(
      children: [
        TextField(controller: name, maxLength: 80,
          decoration: const InputDecoration(labelText: 'Full name', counterText: '')),
        TextField(controller: username, maxLength: 31, autocorrect: false,
          decoration: const InputDecoration(labelText: 'Username', counterText: '')),
        TextField(controller: password, obscureText: true,
          decoration: const InputDecoration(labelText: 'Password')),
        TextField(controller: confirmation, obscureText: true,
          decoration: const InputDecoration(labelText: 'Confirm password')),
        SwitchListTile(contentPadding: EdgeInsets.zero, value: autoLogin,
          onChanged: onAutoLogin, title: const Text('Sign in automatically')),
      ],
    ),
  );
}
