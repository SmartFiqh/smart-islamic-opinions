import 'package:flutter/material.dart';

class AppTheme {
  static ThemeData lightTheme = ThemeData(
    primarySwatch: Colors.green,
    appBarTheme: const AppBarTheme(
      backgroundColor: Color(0xFF1B5E20),
      foregroundColor: Colors.white,
      centerTitle: true,
      elevation: 0,
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
      filled: true,
      fillColor: Colors.white,
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: const Color(0xFF1B5E20),
        foregroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        minimumSize: const Size(double.infinity, 50),
      ),
    ),
    cardTheme: CardTheme(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      elevation: 4,
    ),
    fontFamily: 'Cairo',
    textTheme: const TextTheme(
      headlineMedium: TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
      titleMedium: TextStyle(fontWeight: FontWeight.bold),
      bodyMedium: TextStyle(fontSize: 16),
      bodySmall: TextStyle(fontSize: 14, color: Colors.grey),
    ),
  );
}
