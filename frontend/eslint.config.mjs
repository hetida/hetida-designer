import { defineConfig, globalIgnores } from 'eslint/config';
import globals from 'globals';
import _import from 'eslint-plugin-import';
import jsdoc from 'eslint-plugin-jsdoc';
import angularEslintEslintPlugin from '@angular-eslint/eslint-plugin';
import unicorn from 'eslint-plugin-unicorn';
import preferArrow from 'eslint-plugin-prefer-arrow';
import typescriptEslint from '@typescript-eslint/eslint-plugin';
import { fixupPluginRules } from '@eslint/compat';
import tsParser from '@typescript-eslint/parser';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import js from '@eslint/js';
import { FlatCompat } from '@eslint/eslintrc';
import stylistic from '@stylistic/eslint-plugin';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
  allConfig: js.configs.all
});

export default defineConfig([
  globalIgnores(['**/assets/', './playwright']),
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node
      }
    }
  },
  {
    files: ['**/*.ts'],

    extends: compat.extends(
      'plugin:@typescript-eslint/recommended',
      'plugin:@typescript-eslint/recommended-requiring-type-checking',
      'plugin:prettier/recommended'
    ),

    plugins: {
      import: fixupPluginRules(_import),
      jsdoc,
      '@angular-eslint': angularEslintEslintPlugin,
      unicorn,
      'prefer-arrow': preferArrow,
      '@typescript-eslint': typescriptEslint,
      '@stylistic': stylistic
    },

    languageOptions: {
      parser: tsParser,
      ecmaVersion: 5,
      sourceType: 'module',

      parserOptions: { project: 'tsconfig.eslint.json' }
    },

    rules: {
      'prettier/prettier': 'error',
      '@angular-eslint/component-class-suffix': 'error',
      '@angular-eslint/directive-class-suffix': 'error',
      '@angular-eslint/no-input-rename': 'error',
      '@angular-eslint/no-inputs-metadata-property': 'error',
      '@angular-eslint/no-output-on-prefix': 'error',
      '@angular-eslint/no-output-rename': 'error',
      '@angular-eslint/no-outputs-metadata-property': 'error',
      '@angular-eslint/use-lifecycle-interface': 'error',
      '@angular-eslint/use-pipe-transform-interface': 'error',
      '@angular-eslint/template/no-negated-async': 'off',
      '@typescript-eslint/adjacent-overload-signatures': 'error',
      '@typescript-eslint/array-type': 'off',
      '@typescript-eslint/no-wrapper-object-types': 'error',
      '@typescript-eslint/consistent-type-assertions': 'error',
      '@typescript-eslint/dot-notation': 'error',
      '@typescript-eslint/explicit-function-return-type': 'off',

      '@typescript-eslint/explicit-member-accessibility': [
        'off',
        {
          accessibility: 'explicit'
        }
      ],

      '@typescript-eslint/explicit-module-boundary-types': 'off',
      '@typescript-eslint/indent': 'off',

      '@typescript-eslint/member-ordering': [
        'error',
        {
          default: [
            'static-field',
            'instance-field',
            'static-method',
            'instance-method'
          ]
        }
      ],

      '@typescript-eslint/naming-convention': [
        'off',
        {
          selector: 'variable',
          format: ['camelCase', 'UPPER_CASE'],
          leadingUnderscore: 'forbid',
          trailingUnderscore: 'forbid'
        }
      ],

      '@typescript-eslint/no-empty-function': 'off',
      '@typescript-eslint/no-empty-interface': 'off',
      '@typescript-eslint/no-explicit-any': 'off',

      '@typescript-eslint/no-inferrable-types': [
        'error',
        {
          ignoreParameters: true
        }
      ],

      '@typescript-eslint/no-misused-new': 'error',
      '@typescript-eslint/no-namespace': 'error',
      '@typescript-eslint/no-non-null-assertion': 'error',
      '@typescript-eslint/no-parameter-properties': 'off',

      '@typescript-eslint/no-shadow': [
        'error',
        {
          hoist: 'all'
        }
      ],

      '@typescript-eslint/no-this-alias': 'error',
      '@typescript-eslint/no-unused-expressions': 'error',
      '@typescript-eslint/no-use-before-define': 'off',
      '@typescript-eslint/no-var-requires': 'off',
      '@typescript-eslint/prefer-for-of': 'error',
      '@typescript-eslint/prefer-function-type': 'error',
      '@typescript-eslint/prefer-namespace-keyword': 'error',
      '@typescript-eslint/prefer-readonly': 'error',
      '@stylistic/quotes': ['error', 'single'],

      '@typescript-eslint/strict-boolean-expressions': [
        'off',
        {
          allowNullableObject: true,
          allowNullableBoolean: true,
          allowNullableString: true,
          allowNullableNumber: true
        }
      ],

      '@typescript-eslint/triple-slash-reference': [
        'error',
        {
          path: 'always',
          types: 'prefer-import',
          lib: 'always'
        }
      ],

      '@typescript-eslint/typedef': 'off',
      '@typescript-eslint/unified-signatures': 'error',
      '@typescript-eslint/no-floating-promises': 'off',

      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_'
        }
      ],

      '@typescript-eslint/no-unsafe-argument': 'off',
      '@typescript-eslint/no-unsafe-assignment': 'off',
      '@typescript-eslint/no-unsafe-member-access': 'off',
      '@typescript-eslint/no-unsafe-return': 'off',
      '@typescript-eslint/no-unsafe-call': 'off',
      '@typescript-eslint/unbound-method': 'off',
      '@typescript-eslint/ban-ts-comment': 'off',
      '@typescript-eslint/restrict-template-expressions': 'off',
      'spaced-comment': 'off',
      'arrow-parens': ['off', 'always'],
      'class-methods-use-this': 'off',
      'comma-dangle': 'off',

      complexity: [
        'error',
        {
          max: 20
        }
      ],

      'constructor-super': 'error',
      curly: 'error',
      'default-case': 'error',
      'dot-notation': 'off',
      'eol-last': 'error',
      eqeqeq: ['error', 'always'],
      'guard-for-in': 'error',
      'id-denylist': 'off',
      'id-match': 'off',
      'import/no-deprecated': 'off',

      'import/order': [
        'off',
        {
          alphabetize: {
            caseInsensitive: true,
            order: 'asc'
          },

          'newlines-between': 'ignore',

          groups: [
            ['builtin', 'external', 'internal', 'unknown', 'object', 'type'],
            'parent',
            ['sibling', 'index']
          ],

          distinctGroup: false,
          pathGroupsExcludedImportTypes: [],

          pathGroups: [
            {
              pattern: './',

              patternOptions: {
                nocomment: true,
                dot: true
              },

              group: 'sibling',
              position: 'before'
            },
            {
              pattern: '.',

              patternOptions: {
                nocomment: true,
                dot: true
              },

              group: 'sibling',
              position: 'before'
            },
            {
              pattern: '..',

              patternOptions: {
                nocomment: true,
                dot: true
              },

              group: 'parent',
              position: 'before'
            },
            {
              pattern: '../',

              patternOptions: {
                nocomment: true,
                dot: true
              },

              group: 'parent',
              position: 'before'
            }
          ]
        }
      ],

      indent: 'off',
      'jsdoc/check-alignment': 'off',
      'jsdoc/check-indentation': 'off',
      'jsdoc/newline-after-description': 'off',
      'jsdoc/no-types': 'error',
      'max-classes-per-file': 'off',

      'max-len': [
        'error',
        {
          code: 140
        }
      ],

      'new-parens': 'error',
      'no-bitwise': 'error',
      'no-caller': 'error',
      'no-cond-assign': 'error',

      'no-console': [
        'error',
        {
          allow: [
            'warn',
            'dir',
            'timeLog',
            'assert',
            'clear',
            'count',
            'countReset',
            'group',
            'groupEnd',
            'table',
            'debug',
            'dirxml',
            'error',
            'groupCollapsed',
            'Console',
            'profile',
            'profileEnd',
            'timeStamp',
            'context'
          ]
        }
      ],

      'no-debugger': 'error',
      'no-duplicate-case': 'error',
      'no-duplicate-imports': 'error',
      'no-empty': 'off',
      'no-empty-function': 'off',
      'no-eval': 'error',
      'no-fallthrough': 'error',
      'no-invalid-this': 'error',
      'no-irregular-whitespace': 'error',
      'no-multiple-empty-lines': 'error',
      'no-new-wrappers': 'error',
      'no-redeclare': 'error',
      'no-restricted-imports': ['error', 'rxjs/Rx'],
      'no-shadow': 'off',
      'no-template-curly-in-string': 'error',
      'no-throw-literal': 'error',
      'no-trailing-spaces': 'error',
      'no-undef-init': 'error',
      'no-underscore-dangle': 'off',
      'no-unsafe-finally': 'error',
      'no-unused-expressions': 'off',
      'no-unused-labels': 'error',
      'no-use-before-define': 'off',
      'no-useless-constructor': 'off',
      'no-var': 'error',
      'object-shorthand': 'error',
      'one-var': ['error', 'never'],
      'prefer-arrow/prefer-arrow-functions': 'off',
      'prefer-const': 'error',
      'prefer-template': 'error',
      'quote-props': ['error', 'as-needed'],
      quotes: 'off',
      radix: 'error',
      'unicorn/prefer-switch': 'error',
      'use-isnan': 'error',
      'valid-typeof': 'off'
    }
  },
  {
    files: ['**/*.html'],

    extends: compat.extends(
      'plugin:@angular-eslint/template/recommended',
      'plugin:prettier/recommended'
    ),

    rules: {
      'prettier/prettier': 'error',
      '@angular-eslint/template/no-negated-async': 'off'
    }
  }
]);
