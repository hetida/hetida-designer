import {
  AbstractControl,
  ValidationErrors,
  ValidatorFn,
  Validators
} from '@angular/forms';

export function AllowedCharsValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const value = Validators.pattern(/[^\p{L}\p{N}\p{M}\p{Pc} \.'\()\/=-]/gu);
    const retval = value(control) ? null : { allowedChars: { valid: false } };
    return retval;
  };
}
