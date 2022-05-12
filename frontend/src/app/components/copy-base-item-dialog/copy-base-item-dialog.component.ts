import { Component, EventEmitter, Inject, OnInit } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { select, Store } from '@ngrx/store';
import { BehaviorSubject, combineLatest, Observable } from 'rxjs';
import { first, map, startWith } from 'rxjs/operators';
import { AbstractBaseItem } from 'src/app/model/base-item';
import { BaseItemDialogData } from 'src/app/model/base-item-dialog-data';
import { IAppState } from 'src/app/store/app.state';
import { selectAbstractBaseItems } from 'src/app/store/base-item/base-item.selectors';
import { Utils } from 'src/app/utils/utils';
import { UniqueRevisionTagValidator } from 'src/app/validation/unique-revision-tag-validator';
import { NotOnlyWhitespacesValidator } from 'src/app/validation/not-only-whitespaces-validator';
import { AllowedCharsValidator } from 'src/app/validation/allowed-chars-validator';

@Component({
  selector: 'hd-copy-base-item-dialog',
  templateUrl: './copy-base-item-dialog.component.html',
  styleUrls: ['./copy-base-item-dialog.component.scss']
})
export class CopyBaseItemDialogComponent implements OnInit {
  constructor(
    public dialogRef: MatDialogRef<CopyBaseItemDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: Omit<BaseItemDialogData, 'content'>,
    private readonly store: Store<IAppState>
  ) {}

  /**
   * Form Group for editing of basic workflow/component infos and validation
   */
  infoForm: FormGroup;

  onDelete = new EventEmitter<AbstractBaseItem>();

  private readonly categories$: BehaviorSubject<string[]> = new BehaviorSubject<
    string[]
  >([]);
  public filteredCategories$: Observable<string[]>;

  ngOnInit(): void {
    this.createFormGroup();
    this.store
      .pipe(select(selectAbstractBaseItems))
      .subscribe(abstractBaseItems => {
        this.categories$.next(
          Array.from(
            new Set(
              abstractBaseItems
                .filter(bi => bi.type === this.data.abstractBaseItem.type)
                .map(bi => bi.category)
                .sort(Utils.string.compare)
            )
          )
        );
      });
  }

  public onCancel(): void {
    this.dialogRef.close();
  }

  public onOk(): void {
    this.infoForm.markAllAsTouched();
    if (this.infoForm.invalid) {
      return;
    }
    this.dialogRef.close(this.data.abstractBaseItem);
  }

  public _onDelete(): void {
    this.onDelete.next(this.data.abstractBaseItem);
  }

  /**
   * Checks if form has error (validation)
   */
  public hasError(controlName: string, errorName: string) {
    return this.infoForm.controls[controlName].hasError(errorName);
  }

  public isAllDataPropertiesDisabled(): boolean {
    return Object.entries(this.infoForm.controls).every(
      ([_, control]) => control.disabled
    );
  }

  /**
   * Creates FormGroup for editing of baseItems
   */
  private createFormGroup() {
    this.store
      .pipe(
        select(selectAbstractBaseItems),
        first(),
        map(baseItems =>
          baseItems.filter(
            baseItem => baseItem.groupId === this.data.abstractBaseItem.groupId
          )
        )
      )
      .subscribe(abstractBaseItems => {
        if (
          abstractBaseItems.find(
            abstractBaseItem =>
              abstractBaseItem.id === this.data.abstractBaseItem.id
          ) === undefined
        ) {
          abstractBaseItems.push(this.data.abstractBaseItem);
        }

        this.infoForm = new FormGroup({
          name: new FormControl(
            {
              value: this.data.abstractBaseItem.name,
              disabled: this.data.disabledState.name
            },
            [
              Validators.required,
              Validators.maxLength(60),
              NotOnlyWhitespacesValidator(),
              AllowedCharsValidator()
            ]
          ),
          category: new FormControl(
            {
              value: this.data.abstractBaseItem.category,
              disabled: this.data.disabledState.category
            },
            [
              Validators.required,
              Validators.maxLength(60),
              NotOnlyWhitespacesValidator(),
              AllowedCharsValidator()
            ]
          ),
          description: new FormControl(
            {
              value: this.data.abstractBaseItem.description,
              disabled: this.data.disabledState.description
            },
            [
              Validators.required,
              NotOnlyWhitespacesValidator(),
              AllowedCharsValidator()
            ]
          ),
          tag: new FormControl(
            {
              value: this.data.abstractBaseItem.tag,
              disabled: this.data.disabledState.tag
            },
            [
              Validators.required,
              Validators.maxLength(20),
              UniqueRevisionTagValidator(abstractBaseItems),
              NotOnlyWhitespacesValidator(),
              AllowedCharsValidator()
            ]
          )
        });
        this.infoForm.valueChanges.subscribe(() => {
          if (this.infoForm.invalid) {
            return;
          }

          const withDisabledAttributes = this.infoForm.getRawValue();
          this.data.abstractBaseItem.category = withDisabledAttributes.category.trim();
          this.data.abstractBaseItem.description = withDisabledAttributes.description.trim();
          this.data.abstractBaseItem.name = withDisabledAttributes.name.trim();
          this.data.abstractBaseItem.tag = withDisabledAttributes.tag.trim();
        });

        this.filteredCategories$ = combineLatest([
          this.categories$,
          this.infoForm.get('category').valueChanges.pipe(startWith(''))
        ]).pipe(
          map(([categories, searchTerm]) =>
            categories.filter(cat => {
              if (searchTerm === '') {
                return true;
              }
              return cat.toLowerCase().includes(searchTerm.toLowerCase());
            })
          )
        );
      });
  }
}
