import { Component, EventEmitter, Inject, OnInit } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { select, Store } from '@ngrx/store';
import { BehaviorSubject, combineLatest, Observable } from 'rxjs';
import { first, map, startWith } from 'rxjs/operators';
import { TransformationDialogData } from 'src/app/model/transformation-dialog-data';
import { Utils } from 'src/app/utils/utils';
import { NotOnlyWhitespacesValidator } from 'src/app/validation/not-only-whitespaces-validator';
import { AllowedCharsValidator } from 'src/app/validation/allowed-chars-validator';
import { selectAllTransformations } from '../../store/transformation/transformation.selectors';
import { Transformation } from '../../model/transformation';
import { TransformationState } from 'src/app/store/transformation/transformation.state';
import { UniqueVersionTagValidator } from 'src/app/validation/unique-version-tag-validator';
import { ConfigService } from '../../service/configuration/config.service';

@Component({
  selector: 'hd-copy-transformation-dialog',
  templateUrl: './copy-transformation-dialog.component.html',
  styleUrls: ['./copy-transformation-dialog.component.scss']
})
export class CopyTransformationDialogComponent implements OnInit {
  private apiEndpoint: string;

  constructor(
    public dialogRef: MatDialogRef<CopyTransformationDialogComponent>,
    @Inject(MAT_DIALOG_DATA)
    public data: Omit<TransformationDialogData, 'content'>,
    private readonly transformationStore: Store<TransformationState>,
    private readonly config: ConfigService
  ) {
    this.config.getConfig().subscribe(runtimeConfig => {
      this.apiEndpoint = runtimeConfig.apiEndpoint;
    });
  }

  /**
   * Form Group for editing of basic workflow/component infos and validation
   */
  infoForm: FormGroup;

  onDelete = new EventEmitter<Transformation>();

  private readonly categories$: BehaviorSubject<string[]> = new BehaviorSubject<
    string[]
  >([]);
  public filteredCategories$: Observable<string[]>;

  ngOnInit(): void {
    this.createFormGroup();
    this.transformationStore
      .select(selectAllTransformations)
      .subscribe(transformations => {
        this.categories$.next(
          Array.from(
            new Set(
              transformations
                .filter(
                  transformation =>
                    transformation.type === this.data.transformation.type
                )
                .map(transformation => transformation.category)
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
    this.dialogRef.close(this.data.transformation);
  }

  public _onDelete(): void {
    this.onDelete.next(this.data.transformation);
  }

  public isAllDataPropertiesDisabled(): boolean {
    return Object.entries(this.infoForm.controls).every(
      ([_, control]) => control.disabled
    );
  }

  public getDashboardUrl(): string {
    return `${this.apiEndpoint}/transformations/${this.data.transformation.id}/dashboard`;
  }

  /**
   * Creates FormGroup for editing of transformation
   */
  private createFormGroup() {
    this.transformationStore
      .pipe(
        select(selectAllTransformations),
        first(),
        map(transformations =>
          transformations.filter(
            transformation =>
              transformation.revision_group_id ===
              this.data.transformation.revision_group_id
          )
        )
      )
      .subscribe(transformations => {
        if (
          transformations.find(
            transformation => transformation.id === this.data.transformation.id
          ) === undefined
        ) {
          transformations.push(this.data.transformation);
        }

        this.infoForm = new FormGroup({
          name: new FormControl(
            {
              value: this.data.transformation.name,
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
              value: this.data.transformation.category,
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
              value: this.data.transformation.description,
              disabled: this.data.disabledState.description
            },
            [NotOnlyWhitespacesValidator(), AllowedCharsValidator()]
          ),
          tag: new FormControl(
            {
              value: this.data.transformation.version_tag,
              disabled: this.data.disabledState.tag
            },
            [
              Validators.required,
              Validators.maxLength(20),
              UniqueVersionTagValidator(transformations),
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
          this.data.transformation.category =
            withDisabledAttributes.category.trim();
          this.data.transformation.description =
            withDisabledAttributes.description.trim();
          this.data.transformation.name = withDisabledAttributes.name.trim();
          this.data.transformation.version_tag =
            withDisabledAttributes.tag.trim();
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
