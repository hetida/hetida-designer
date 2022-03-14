import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

export function PythonKeywordBlacklistValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const pythonKeywords = [
      'False',
      'await',
      'else',
      'import',
      'pass',
      'None',
      'break',
      'except',
      'in',
      'raise',
      'True',
      'class',
      'finally',
      'is',
      'return',
      'and',
      'continue',
      'for',
      'lambda',
      'try',
      'as',
      'def',
      'from',
      'nonlocal',
      'while',
      'assert',
      'del',
      'global',
      'not',
      'with',
      'async',
      'elif',
      'if',
      'or',
      'yield'
    ];
    const noViolation = pythonKeywords.every(value => value !== control.value);
    return noViolation ? null : { pythonKeywordBlacklist: { valid: false } };
  };
}
