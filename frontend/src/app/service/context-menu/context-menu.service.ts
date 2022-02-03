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
 * The function "disposeAllContextMenus" should be called in a global manner attached to mousedown event,
 * to close opened menus on click somewhere else.
 */
@Injectable({
  providedIn: 'root'
})
export class ContextMenuService {
  /**
   * Opened overlay references
   */
  private overlayRefs: OverlayRef[] = [];

  constructor(private readonly overlay: Overlay) {}

  /**
   *
   * Register an opened overlayRef.
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
   * Open a context menu.
   *
   * Uses angular material overlay API to open the menu, global position strategy will be used,
   * normally you would like to open a context menu near the mouse position, therefore supporting other strategies is not planned.
   *
   *  Internally calls "registerContextMenu" so no need to call it separately.
   *
   *
   * @param component An instance of ComponentPortal, you can create one with "new ComponentPortal(FooComponent)".
   * Import from "import { ComponentPortal } from '@angular/cdk/portal';"
   * @param position x and y positions where the menu should appear, in most cases clientX and clientY from mouseEvent will do.
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
