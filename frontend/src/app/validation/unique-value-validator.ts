import {
  AbstractControl,
  FormArray,
  FormGroup,
  ValidationErrors,
  ValidatorFn
} from '@angular/forms';
import { Utils } from '../utils/utils';

export function UniqueValueValidator(formControlName: string): ValidatorFn {
  const invalidValidatorUsageErrorMessage =
    'You can apply this validator on a FormArray, the child has to be a FormGroup';

  return (control: AbstractControl): ValidationErrors | null => {
    if (!(control instanceof FormArray)) {
      throw Error(invalidValidatorUsageErrorMessage);
    }
    const formArrayHasFormGroups = control.controls.some(
      c => c instanceof FormGroup
    );
    if (!formArrayHasFormGroups) {
      return null;
    }

    let hasDuplicateValue = false;
    control.controls.forEach((currentFormGroup, index) => {
      const currentFormControl = currentFormGroup.get(formControlName);
      Utils.assert(
        currentFormControl,
        `formControl with name ${formControlName} not found`
      );

      if (
        Utils.isNullOrUndefined(currentFormControl.value) ||
        (Utils.isDefined(currentFormControl.value) &&
          Utils.string.isEmpty(currentFormControl.value))
      ) {
        return;
      }
      hasDuplicateValue = control.controls
        .filter((_, i) => i !== index)
        .map(formGroup => formGroup.get(formControlName)?.value)
        .some(value => currentFormControl.value === value);

      const error = hasDuplicateValue ? { uniqueValue: true } : null;

      const controlHasUniqueValueError =
        currentFormControl.errors && 'uniqueValue' in currentFormControl.errors;

      if (Utils.isNullOrUndefined(error) && controlHasUniqueValueError) {
        currentFormControl.setErrors(null);
      } else if (!Utils.isNullOrUndefined(error)) {
        currentFormControl.setErrors(error);
      }

      currentFormControl.markAsTouched();
    });

    return hasDuplicateValue
      ? { formGroupHasDuplicateValue: { valid: false } }
      : null;
  };
}
