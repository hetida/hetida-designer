import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

export function PythonIdentifierValidator(canBeEmpty: boolean): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    if (control.value === '' && canBeEmpty) {
      return null;
    }
    // matches python 2.x identifiers, python 3 technically allows unicode characters(!), which we can't handle with a regex
    // https://docs.python.org/3/reference/lexical_analysis.html#identifiers
    const pythonIdentifierRegex = new RegExp('^[_a-zA-Z]\\w*$');
    const noViolation = pythonIdentifierRegex.test(control.value);
    return noViolation ? null : { pythonIdentifier: { valid: false } };
  };
}
