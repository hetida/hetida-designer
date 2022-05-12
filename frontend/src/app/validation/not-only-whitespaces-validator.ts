import {
  AbstractControl,
  ValidationErrors,
  ValidatorFn,
  Validators
} from '@angular/forms';

export function NotOnlyWhitespacesValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const val = Validators.pattern(/.*[^ ].*/);
    return val(control) ? { notOnlyWhitespaces: { valid: false } } : null;
  };
}
