import { Component, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { Store } from '@ngrx/store';
import { combineLatest, Observable } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { AbstractBaseItem } from 'src/app/model/base-item';
import { BaseItemActionService } from 'src/app/service/base-item/base-item-action.service';
import { PopoverService } from 'src/app/service/popover/popover.service';
import { Utils } from 'src/app/utils/utils';
import { AuthService } from '../../../auth/auth.service';
import { BaseItemService } from '../../../service/base-item/base-item.service';
import { IAppState } from '../../../store/app.state';
import { selectBaseItemsByCategory } from '../../../store/base-item/base-item.selectors';
import { TransformationRevisionService } from '../../../service/transformation-revision/transformation-revision.service';
import { TransformationRevisionState } from '../../../store/transformation-revision/transformation-revision.state';
import { selectAllTransformationRevisions } from '../../../store/transformation-revision/transformaton-revision.selectors';

@Component({
  selector: 'hd-navigation-container',
  templateUrl: './navigation-container.component.html',
  styleUrls: ['./navigation-container.component.scss']
})
export class NavigationContainerComponent implements OnInit {
  constructor(
    private readonly _store: Store<IAppState>,
    private readonly transformationRevisionStore: Store<TransformationRevisionState>,
    private readonly _baseItemService: BaseItemService,
    private readonly transformationRevisionService: TransformationRevisionService,
    private readonly _popover: PopoverService,
    private readonly _baseItemAction: BaseItemActionService,
    private readonly authService: AuthService
  ) {}

  readonly searchFilter = new FormControl('');
  readonly typeFilter = new FormControl(BaseItemType.WORKFLOW);

  // TODO transformationRevisionsByCategory
  abstractBaseItemsByCategory: [string, AbstractBaseItem[]][];

  getFilterState(type: string): boolean {
    return (this.typeFilter.value as string) === type;
  }

  get filterChanges(): Observable<BaseItemType> {
    return this.typeFilter.valueChanges;
  }

  get searchFilterChanges(): Observable<string> {
    return this.searchFilter.valueChanges;
  }

  ngOnInit(): void {
    this.authService.isAuthenticated$().subscribe(() => {
      this._baseItemService.fetchBaseItems();
      this.transformationRevisionService.getTransformationRevisions();
    });
    // TODO remove after new filter selector is implemented
    this.transformationRevisionStore
      .select(selectAllTransformationRevisions)
      .subscribe(transformationRevisions => {
        console.log('hello from nav container', transformationRevisions);
      });

    combineLatest([this.filterChanges, this.searchFilterChanges])
      .pipe(
        switchMap(([baseItemType, searchString]) =>
          this._store.select(
            // TODO create and unit test this selector for transformationRevisions
            // TODO sort alphabetically in the new selector
            selectBaseItemsByCategory(baseItemType, searchString)
          )
        )
      )
      .subscribe(filteredAbstractBaseItems => {
        this.abstractBaseItemsByCategory = Object.entries(
          filteredAbstractBaseItems
        ).sort(([categoryNameA], [categoryNameB]) =>
          Utils.string.compare(categoryNameA, categoryNameB)
        );
      });

    this.filterChanges.subscribe(() => this._popover.closePopover());
    this.typeFilter.updateValueAndValidity({ emitEvent: true });
    this.searchFilter.updateValueAndValidity({ emitEvent: true });
  }

  newWorkflow(): void {
    this._baseItemAction.newWorkflow();
  }

  newComponent(): void {
    this._baseItemAction.newComponent();
  }

  closePopover(): void {
    this._popover.closePopover();
  }

  trackByBaseItemId(_: number, abstractBaseItem: AbstractBaseItem) {
    return abstractBaseItem.id;
  }
}
