// @ts-check
const eslint = require('@eslint/js');
const { defineConfig } = require('eslint/config');
const tseslint = require('typescript-eslint');
const angular = require('angular-eslint');

module.exports = defineConfig([
  {
    files: ['**/*.ts'],
    extends: [
      eslint.configs.recommended,
      tseslint.configs.recommended,
      tseslint.configs.stylistic,
      angular.configs.tsRecommended,
    ],
    processor: angular.processInlineTemplates,
    // Información de tipos, solo para las reglas que la necesitan (más abajo). No se usa el
    // paquete recommendedTypeChecked: sus reglas no-unsafe-* dan mucho ruido con el JSON de la API.
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: __dirname,
      },
    },
    rules: {
      // Con tipos: `if (this.cargando)` en lugar de `this.cargando()` es siempre verdadero.
      '@angular-eslint/no-uncalled-signals': 'error',
      // Con tipos: promesas sin await, también en los tests (`fixture.whenStable()`).
      '@typescript-eslint/no-floating-promises': 'error',
      '@angular-eslint/computed-must-return': 'error',
      '@angular-eslint/directive-selector': [
        'error',
        {
          type: 'attribute',
          prefix: 'app',
          style: 'camelCase',
        },
      ],
      '@angular-eslint/component-selector': [
        'error',
        {
          type: 'element',
          prefix: 'app',
          style: 'kebab-case',
        },
      ],
    },
  },
  {
    files: ['**/*.html'],
    extends: [angular.configs.templateRecommended, angular.configs.templateAccessibility],
    rules: {
      // Sin type, un botón dentro de un formulario lo envía.
      '@angular-eslint/template/button-has-type': 'error',
      // Un tabindex positivo desordena la navegación con teclado.
      '@angular-eslint/template/no-positive-tabindex': 'error',
      // $any() se salta strictTemplates.
      '@angular-eslint/template/no-any': 'error',
      '@angular-eslint/template/no-duplicate-attributes': 'error',
    },
  },
]);
