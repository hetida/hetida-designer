import { Component, Input, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { PopoverService } from 'src/app/service/popover/popover.service';
import { selectActiveTabItem } from 'src/app/store/tab-item/tab-item.selectors';
import { Utils } from 'src/app/utils/utils';
import { IAppState } from '../../../store/app.state';
import { Transformation } from '../../../model/new-api/transformation';

@Component({
  selector: 'hd-navigation-category',
  templateUrl: './navigation-category.component.html',
  styleUrls: ['./navigation-category.component.scss']
})
export class NavigationCategoryComponent implements OnInit {
  private _transformations: Transformation[];

  @Input()
  set transformations(transformations: Transformation[]) {
    this._transformations = transformations.sort(
      (transformationA, transformationB) =>
        Utils.string.compare(transformationA.name, transformationB.name)
    );
  }

  get transformations(): Transformation[] {
    return this._transformations;
  }

  @Input()
  category = '';

  public activeTransformationId = '';

  constructor(
    private readonly store: Store<IAppState>,
    private readonly popover: PopoverService
  ) {}

  ngOnInit() {
    this.store.select(selectActiveTabItem).subscribe(activeTabItem => {
      if (activeTabItem === null) {
        this.activeTransformationId = '';
      } else {
        this.activeTransformationId = activeTabItem.transformationId;
      }
    });
  }

  public closePopover(): void {
    this.popover.closePopover();
  }
}
