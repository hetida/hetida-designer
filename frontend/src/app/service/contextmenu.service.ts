import { Overlay, OverlayRef } from '@angular/cdk/overlay';
import { ComponentPortal } from '@angular/cdk/portal';
import { ComponentRef, Injectable } from '@angular/core';

interface ContextMenuPosition {
  x: number;
  y: number;
}

interface ContextMenuRefs<T> {
  overlayRef: OverlayRef;
  componentPortalRef: ComponentRef<T>;
}

/**
 * Context menu service. Provides a handy way to open context menus.
 *
 * The funktion "disposeAllContextMenus" should be called in an global manner attached to mousedown event,
 * to close opened manus on click somewhere else.
 */
@Injectable({
  providedIn: 'root'
})
export class ContextmenuService {
  /**
   * Opened overlay references
   */
  private overlayRefs: OverlayRef[] = [];

  constructor(private readonly overlay: Overlay) {}

  /**
   *
   * Register a opened overlayRef.
   *
   * @param overlayRef Opened overlayRef
   */
  registerContextMenu(overlayRef: OverlayRef) {
    this.overlayRefs.push(overlayRef);
  }

  /**
   * Removes all context menus from dom
   */
  disposeAllContextMenus() {
    this.overlayRefs.forEach(o => o.dispose());
    this.overlayRefs = [];
  }

  /**
   * Open a context menü.
   *
   * Uses angular material overlay API to open the menu, global position strategy will be used,
   * normaly you would like to open a context menu near the mouse position, therefore supporting other strategies are not planed.
   *
   *  calls internally "registerContextMenu" so dont need to call it.
   *
   *
   * @param component An instance of ComponentPortal, you can create one with "new ComponentPortal(FooComponent)".
   * Import from "import { ComponentPortal } from '@angular/cdk/portal';"
   * @param position x and y positions where the mene should be appaer, in the most cases clientX and clientY from mouseEvent would do it.
   */
  openContextMenu<T>(
    component: ComponentPortal<T>,
    position: ContextMenuPosition
  ): ContextMenuRefs<T> {
    const globalPosition = this.overlay
      .position()
      .global()
      .top(`${position.y}px`)
      .left(`${position.x}px`);
    const overlayRef = this.overlay.create({
      positionStrategy: globalPosition,
      hasBackdrop: false
    });
    this.registerContextMenu(overlayRef);
    const componentPortalRef = overlayRef.attach(component);

    return {
      componentPortalRef,
      overlayRef
    };
  }
}
