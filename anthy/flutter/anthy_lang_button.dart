// AnThy Remote: quick language picker shown next to the Settings button
// (desktop: top-right of the main window). Copied into the RustDesk source by
// anthy/apply_branding.py at build time.
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_hbb/common.dart';
import 'package:flutter_hbb/consts.dart';
import 'package:flutter_hbb/models/platform_model.dart';

class AnthyLangButton extends StatefulWidget {
  const AnthyLangButton({Key? key}) : super(key: key);

  @override
  State<AnthyLangButton> createState() => _AnthyLangButtonState();
}

class _AnthyLangButtonState extends State<AnthyLangButton> {
  List<List<String>> _langs = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final list = jsonDecode(await bind.mainGetLangs()) as List<dynamic>;
      if (!mounted) return;
      setState(() {
        _langs = list
            .map((e) => [e[0].toString(), e[1].toString()])
            .toList();
      });
    } catch (_) {}
  }

  Future<void> _select(String key) async {
    await bind.mainSetLocalOption(key: kCommConfKeyLang, value: key);
    reloadAllWindows();
    bind.mainChangeLanguage(lang: key);
  }

  @override
  Widget build(BuildContext context) {
    if (isOptionFixed(kCommConfKeyLang) == true) {
      return const SizedBox.shrink();
    }
    final String defKey = defaultOptionLang.toString();
    final items = <List<String>>[
      [defKey, translate('Default')],
      ..._langs,
    ];
    final stored = bind.mainGetLocalOption(key: kCommConfKeyLang);
    final current =
        items.any((e) => e[0] == stored) ? stored : defKey;
    final color = Theme.of(context).textTheme.titleLarge?.color;

    return PopupMenuButton<String>(
      tooltip: translate('Language'),
      padding: EdgeInsets.zero,
      onSelected: _select,
      itemBuilder: (context) => items
          .map((e) => PopupMenuItem<String>(
                value: e[0],
                height: 34,
                child: Row(children: [
                  SizedBox(
                    width: 22,
                    child: e[0] == current
                        ? const Icon(Icons.check, size: 16)
                        : null,
                  ),
                  Text(e[1]),
                ]),
              ))
          .toList(),
      child: SizedBox(
        width: kDesktopRemoteTabBarHeight + 8,
        height: kDesktopRemoteTabBarHeight - 1,
        child: Icon(Icons.translate,
            size: 15, color: color?.withOpacity(0.7)),
      ),
    );
  }
}
