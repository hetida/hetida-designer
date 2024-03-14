import { Component, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { Store } from '@ngrx/store';
import { combineLatest, Observable } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { TransformationType } from 'src/app/enums/transformation-type';
import { TransformationActionService } from 'src/app/service/transformation/transformation-action.service';
import { PopoverService } from 'src/app/service/popover/popover.service';
import { AuthService } from '../../../auth/auth.service';
import { TransformationService } from '../../../service/transformation/transformation.service';
import { TransformationState } from '../../../store/transformation/transformation.state';
import {
  selectAllTransformations,
  selectTransformationsByCategoryAndName
} from '../../../store/transformation/transformation.selectors';
import { Transformation } from 'src/app/model/transformation';
import { KeyValue } from '@angular/common';
import { Utils } from '../../../utils/utils';
import { QueryParameterService } from 'src/app/service/query-parameter/query-parameter.service';
import { TabItemService } from 'src/app/service/tab-item/tab-item.service';
import { NotificationService } from 'src/app/service/notifications/notification.service';

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
    private readonly authService: AuthService,
    private readonly queryParameterService: QueryParameterService,
    private readonly tabItemService: TabItemService,
    private readonly notificationService: NotificationService
  ) {}

  readonly searchFilter = new FormControl('');
  readonly typeFilter = new FormControl(TransformationType.WORKFLOW);

  transformationsByCategory: { [category: string]: Transformation[] };

  getFilterState(type: string): boolean {
    return (this.typeFilter.value as string) === type;
  }

  get filterChanges(): Observable<TransformationType> {
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
        switchMap(([transformationType, searchString]) =>
          this.transformationStore.select(
            selectTransformationsByCategoryAndName(
              transformationType,
              searchString
            )
          )
        )
      )
      .subscribe(filteredTransformations => {
        this.transformationsByCategory = filteredTransformations;
      });

    this.filterChanges.subscribe(() => this.popoverService.closePopover());
    this.typeFilter.updateValueAndValidity({ emitEvent: true });
    this.searchFilter.updateValueAndValidity({ emitEvent: true });

    this.addTabsFromQueryParameters();
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

  private async addTabsFromQueryParameters(): Promise<void> {
    const ids = await this.queryParameterService.getIdsFromQueryParameters();

    this.transformationStore
      .select(selectAllTransformations)
      .subscribe(transformations => {
        for (const id of ids) {
          if (
            transformations.find(transformation => transformation.id === id) !==
            undefined
          ) {
            this.tabItemService.addTransformationTab(id);
            // ngOnInit runs two times, on the first run the store is always empty, so we ignore missing transformations
          } else if (transformations.length > 0) {
            // only the first missing transformation triggers an pop-up message
            this.notificationService.warn(
              'Could not find transformation, see console for details.'
            );
            // to look after all missing transformations
            console.warn(`Could not find transformation with id '${id}'`);
          }
        }
      });
  }
}
