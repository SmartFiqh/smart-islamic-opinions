import 'package:flutter/material.dart';

/// عتبات بسيطة لتصنيف حجم الشاشة
class Breakpoints {
  static const double tablet = 700;
  static const double desktop = 1100;
}

bool isDesktop(BuildContext context) =>
    MediaQuery.of(context).size.width >= Breakpoints.desktop;

bool isTablet(BuildContext context) =>
    MediaQuery.of(context).size.width >= Breakpoints.tablet &&
    MediaQuery.of(context).size.width < Breakpoints.desktop;

/// يُغلّف محتوى الشاشة بحيث يبقى بعرض كامل على الجوال،
/// ويتوسّط بعرض أقصى مريح للقراءة على الشاشات الكبيرة (ديسكتوب/ويب/تابلت).
/// استخدمه حول جسم أي Scaffold: `body: ResponsiveCenter(child: ...)`.
class ResponsiveCenter extends StatelessWidget {
  final Widget child;
  final double maxWidth;

  const ResponsiveCenter({
    super.key,
    required this.child,
    this.maxWidth = 900,
  });

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.topCenter,
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: maxWidth),
        child: child,
      ),
    );
  }
}

/// شبكة استجابة بسيطة: عمود واحد على الجوال، عمودان أو أكثر على الشاشات الواسعة.
/// مفيدة لعرض قوائم البطاقات (المذاهب، المسائل...) بشكل أفضل على الديسكتوب.
class ResponsiveGrid extends StatelessWidget {
  final List<Widget> children;
  final double itemMinWidth;
  final double spacing;

  const ResponsiveGrid({
    super.key,
    required this.children,
    this.itemMinWidth = 340,
    this.spacing = 12,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = (constraints.maxWidth / itemMinWidth).floor().clamp(1, 4);
        if (columns <= 1) {
          return Column(
            children: children
                .map((c) => Padding(padding: EdgeInsets.only(bottom: spacing), child: c))
                .toList(),
          );
        }
        return Wrap(
          spacing: spacing,
          runSpacing: spacing,
          children: children
              .map(
                (c) => SizedBox(
                  width: (constraints.maxWidth - spacing * (columns - 1)) / columns,
                  child: c,
                ),
              )
              .toList(),
        );
      },
    );
  }
}
