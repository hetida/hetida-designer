import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';
import { ShowPopover } from '../model/show-popover';
/**
 * TODO move to popover folder
 */
@Injectable({
  providedIn: 'root'
})
export class PopoverService {
  private readonly popoverState$: Subject<ShowPopover | null> = new Subject();

  get onPopover() {
    return this.popoverState$.asObservable();
  }

  public closePopover(): void {
    this.popoverState$.next(null);
  }

  public showPopover(
    itemId: string,
    posX: number,
    posY: number | null,
    extendRight: boolean = true,
    showPreview: boolean = true
  ): void {
    this.popoverState$.next({
      itemId,
      posX,
      posY,
      extendRight,
      visible: true,
      showPreview
    });
  }
}
