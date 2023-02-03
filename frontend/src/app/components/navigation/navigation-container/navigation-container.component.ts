import { Component, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { Store } from '@ngrx/store';
import { combineLatest, Observable } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { TransformationActionService } from 'src/app/service/transformation/transformation-action.service';
import { PopoverService } from 'src/app/service/popover/popover.service';
import { AuthService } from '../../../auth/auth.service';
import { TransformationService } from '../../../service/transformation/transformation.service';
import { TransformationState } from '../../../store/transformation/transformation.state';
import { selectTransformationsByCategoryAndName } from '../../../store/transformation/transformation.selectors';
import { Transformation } from 'src/app/model/transformation';
import { KeyValue } from '@angular/common';
import { Utils } from '../../../utils/utils';

@Component({
  selector: 'hd-navigation-container',
  templateUrl: './navigation-container.component.html',
  styleUrls: ['./navigation-container.component.scss']
})
export class NavigationContainerComponent implements OnInit {
  constructor(
    private readonly transformationStore: Store<TransformationState>,
    private readonly transformationService: TransformationService,
    private readonly popoverService: PopoverService,
    private readonly transformationActionService: TransformationActionService,
    private readonly authService: AuthService
  ) {}

  readonly searchFilter = new FormControl('');
  readonly typeFilter = new FormControl(BaseItemType.WORKFLOW);

  transformationsByCategory: { [category: string]: Transformation[] };

  getFilterState(type: string): boolean {
    return (this.typeFilter.value as string) === type;
  }

  get filterChanges(): Observable<BaseItemType> {
    return this.typeFilter.valueChanges;
  }

  get searchFilterChanges(): Observable<string> {
    return this.searchFilter.valueChanges;
  }

  trackCategory(_index: number, category: any) {
    return category.key;
  }

  ngOnInit(): void {
    this.authService.isAuthenticated$().subscribe(() => {
      this.transformationService.fetchAllTransformations();
    });

    combineLatest([this.filterChanges, this.searchFilterChanges])
      .pipe(
        switchMap(([baseItemType, searchString]) =>
          this.transformationStore.select(
            selectTransformationsByCategoryAndName(baseItemType, searchString)
          )
        )
      )
      .subscribe(filteredTransformations => {
        this.transformationsByCategory = filteredTransformations;
      });

    this.filterChanges.subscribe(() => this.popoverService.closePopover());
    this.typeFilter.updateValueAndValidity({ emitEvent: true });
    this.searchFilter.updateValueAndValidity({ emitEvent: true });
  }

  newWorkflow(): void {
    this.transformationActionService.newWorkflow();
  }

  newComponent(): void {
    this.transformationActionService.newComponent();
  }

  closePopover(): void {
    this.popoverService.closePopover();
  }

  sortByCategoryAlphabetically(
    categoryA: KeyValue<string, Transformation[]>,
    categoryB: KeyValue<string, Transformation[]>
  ): number {
    return Utils.string.compare(categoryA.key, categoryB.key);
  }
}
