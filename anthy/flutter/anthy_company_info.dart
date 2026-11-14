// AnThy Remote: company name + hotline, shown at the bottom of the main screen.
// Copied into the RustDesk source by anthy/apply_branding.py at build time;
// __COMPANY__, __TAXCODE__, __HOTLINE__ and __WEBSITE__ are filled in from anthy/brand.json.
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

const String kAnthyCompany = '__COMPANY__';
const String kAnthyHotline = '__HOTLINE__';
const String kAnthyTaxCode = '__TAXCODE__';
const String kAnthyWebsite = '__WEBSITE__';

class AnthyCompanyInfo extends StatelessWidget {
  const AnthyCompanyInfo({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final color = Theme.of(context).textTheme.titleLarge?.color;
    final tel = kAnthyHotline.replaceAll(RegExp(r'[^0-9+]'), '');
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        border: Border(
            top: BorderSide(color: Theme.of(context).dividerColor, width: 0.5)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            kAnthyCompany,
            textAlign: TextAlign.center,
            style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: color?.withOpacity(0.85)),
          ),
          if (kAnthyTaxCode.isNotEmpty) ...[
            const SizedBox(height: 2),
            Text(
              'MST: $kAnthyTaxCode',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12, color: color?.withOpacity(0.75)),
            ),
          ],
          const SizedBox(height: 4),
          InkWell(
            onTap: () async {
              try {
                await launchUrl(Uri.parse('tel:$tel'));
              } catch (_) {}
            },
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.phone, size: 14, color: Color(0xFF1E2BD8)),
                const SizedBox(width: 4),
                Text(
                  'Hotline: $kAnthyHotline',
                  style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1E2BD8)),
                ),
              ],
            ),
          ),
          if (kAnthyWebsite.isNotEmpty) ...[
            const SizedBox(height: 2),
            InkWell(
              onTap: () async {
                try {
                  final url = kAnthyWebsite.startsWith('http')
                      ? kAnthyWebsite
                      : 'https://$kAnthyWebsite';
                  await launchUrl(Uri.parse(url),
                      mode: LaunchMode.externalApplication);
                } catch (_) {}
              },
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.language, size: 14, color: Color(0xFF1E2BD8)),
                  const SizedBox(width: 4),
                  Text(
                    'Web: $kAnthyWebsite',
                    style: const TextStyle(
                        fontSize: 13,
                        color: Color(0xFF1E2BD8),
                        decoration: TextDecoration.underline,
                        decorationColor: Color(0xFF1E2BD8)),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}
