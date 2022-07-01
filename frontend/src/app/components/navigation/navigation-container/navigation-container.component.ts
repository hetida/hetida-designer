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

@Component({
  selector: 'hd-navigation-container',
  templateUrl: './navigation-container.component.html',
  styleUrls: ['./navigation-container.component.scss']
})
export class NavigationContainerComponent implements OnInit {
  constructor(
    private readonly _store: Store<IAppState>,
    private readonly _baseItemService: BaseItemService,
    private readonly _popover: PopoverService,
    private readonly _baseItemAction: BaseItemActionService,
    private readonly authService: AuthService
  ) {}

  readonly searchFilter = new FormControl('');
  readonly typeFilter = new FormControl(BaseItemType.WORKFLOW);

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
    });
    combineLatest([this.filterChanges, this.searchFilterChanges])
      .pipe(
        switchMap(([baseItemType, searchString]) =>
          this._store.select(
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
