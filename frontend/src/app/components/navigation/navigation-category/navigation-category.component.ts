import { Component, Input, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { PopoverService } from 'src/app/service/popover/popover.service';
import { selectActiveTabItem } from 'src/app/store/tab-item/tab-item.selectors';
import { Utils } from 'src/app/utils/utils';
import { AbstractBaseItem } from '../../../model/base-item';
import { IAppState } from '../../../store/app.state';

@Component({
  selector: 'hd-navigation-category',
  templateUrl: './navigation-category.component.html',
  styleUrls: ['./navigation-category.component.scss']
})
export class NavigationCategoryComponent implements OnInit {
  public filteredAbstractBaseItems$: Observable<AbstractBaseItem[]>;

  private _abstractBaseItems: AbstractBaseItem[];

  @Input()
  set abstractBaseItem(abstractBaseItems: AbstractBaseItem[]) {
    this._abstractBaseItems = abstractBaseItems.sort(
      (abstractBaseItemA, abstractBaseItemB) =>
        Utils.string.compare(abstractBaseItemA.name, abstractBaseItemB.name)
    );
  }

  get abstractBaseItem(): AbstractBaseItem[] {
    return this._abstractBaseItems;
  }

  @Input()
  category = '';

  public activeBaseItemId = '';

  constructor(
    private readonly store: Store<IAppState>,
    private readonly popover: PopoverService
  ) {}

  ngOnInit() {
    this.store.select(selectActiveTabItem).subscribe(activeTabItem => {
      if (activeTabItem === null) {
        this.activeBaseItemId = '';
      } else {
        this.activeBaseItemId = activeTabItem.baseItemId;
      }
    });
  }

  public closePopover(): void {
    this.popover.closePopover();
  }
}
