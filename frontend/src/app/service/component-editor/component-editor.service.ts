// import { Injectable } from '@angular/core';
// import { Store } from '@ngrx/store';
// import { TestWiring } from 'hd-wiring';
// import { iif, Observable, of } from 'rxjs';
// import { finalize, switchMap, switchMapTo, tap } from 'rxjs/operators';
// import { ComponentBaseItem } from '../../model/component-base-item';
// import { IAppState } from '../../store/app.state';
// import { isComponentBaseItem } from '../../store/base-item/base-item-guards';
// import {
//   addBaseItem,
//   patchComponentProperties,
//   putBaseItem
// } from '../../store/base-item/base-item.actions';
// import {
//   selectAbstractBaseItemById,
//   selectComponentBaseItemById
// } from '../../store/base-item/base-item.selectors';
// import {
//   setExecutionFinished,
//   setExecutionProtocol,
//   setExecutionRunning
// } from '../../store/execution-protocol/execution-protocol.actions';
// import { ComponentHttpService } from '../http-service/component-http.service';

// @Injectable({
//   providedIn: 'root'
// })
// export class ComponentEditorService {
//   constructor(
//     private readonly componentHttpService: ComponentHttpService,
//     private readonly store: Store<IAppState>
//   ) {}

//   getComponent(id: string): Observable<ComponentBaseItem> {
//     return this.store
//       .select(selectAbstractBaseItemById(id))
//       .pipe(
//         switchMap(baseItem =>
//           iif(
//             () => isComponentBaseItem(baseItem),
//             this.store.select(selectComponentBaseItemById(id)),
//             this._patchComponentProperties(id)
//           )
//         )
//       );
//   }

//   updateComponent(componentBaseItem: ComponentBaseItem) {
//     this.componentHttpService
//       .updateComponent(componentBaseItem)
//       .subscribe(result => {
//         this.store.dispatch(putBaseItem(result));
//       });
//   }

//   createComponent(componentRevision: ComponentBaseItem) {
//     return this.componentHttpService.createComponent(componentRevision).pipe(
//       tap(() => {
//         this.store.dispatch(addBaseItem(componentRevision));
//       })
//     );
//   }

//   testComponent(id: string, wiring: TestWiring): Observable<ComponentBaseItem> {
//     return of(null).pipe(
//       tap(() => this.store.dispatch(setExecutionRunning())),
//       switchMapTo(this.componentHttpService.executeComponent(id, wiring)),
//       tap(result => this.store.dispatch(setExecutionProtocol(result))),
//       finalize(() => this.store.dispatch(setExecutionFinished()))
//     );
//   }

//   bindWiringToComponent(componentId: string, workflowWiring: TestWiring) {
//     return this.componentHttpService
//       .bindWiringToComponent(componentId, workflowWiring)
//       .pipe(
//         tap(result => {
//           this.store.dispatch(putBaseItem(result));
//         })
//       );
//   }

//   private _patchComponentProperties(baseItemId: string) {
//     return this.componentHttpService.getComponent(baseItemId).pipe(
//       tap(componentBaseItem => {
//         return this.store.dispatch(patchComponentProperties(componentBaseItem));
//       })
//     );
//   }
// }
