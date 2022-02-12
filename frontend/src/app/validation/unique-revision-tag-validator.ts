import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';
import { AbstractBaseItem } from '../model/base-item';

export function UniqueRevisionTagValidator(
  revisionItems: AbstractBaseItem[]
): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    if (
      revisionItems.filter(item => item.tag.trim() === control.value.trim())
        .length > 1
    ) {
      return { revisionTag: { valid: false } };
    }
    return null;
  };
}
