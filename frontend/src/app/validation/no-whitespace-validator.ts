import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

export function NoWhitespaceValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    if (control.value.length !== control.value.trim().length) {
      return { noWhitespace: { valid: false } };
    }

    return null;
  };
}
