import { Injectable } from '@angular/core';
import { Store } from '@ngrx/store';
import { Wiring } from 'hd-wiring';
import { iif, Observable, of } from 'rxjs';
import { finalize, switchMap, switchMapTo, tap } from 'rxjs/operators';
import { ComponentBaseItem } from '../model/component-base-item';
import { IAppState } from '../store/app.state';
import { isComponentBaseItem } from '../store/base-item/base-item-guards';
import {
    addBaseItem,
    patchComponentProperties,
    putBaseItem,
    removeBaseItem
} from '../store/base-item/base-item.actions';
import {
    selectAbstractBaseItemById,
    selectComponentBaseItemById
} from '../store/base-item/base-item.selectors';
import {
    setExecutionFinished,
    setExecutionProtocol,
    setExecutionRunning
} from '../store/execution-protocol/execution-protocol.actions';
import { ComponentHttpService } from './http-service/component-http.service';
import { LocalStorageService } from './local-storage/local-storage.service';

@Injectable({
    providedIn: 'root'
})
export class ComponentEditorService {
    constructor(
        private readonly componentHttpService: ComponentHttpService,
        private readonly store: Store<IAppState>,
        private readonly localStorageService: LocalStorageService
    ) { }

    getComponent(id: string): Observable<ComponentBaseItem> {
        return this.store
            .select(selectAbstractBaseItemById(id))
            .pipe(
                switchMap(baseItem =>
                    iif(
                        () => isComponentBaseItem(baseItem),
                        this.store.select(selectComponentBaseItemById(id)),
                        this._patchComponentProperties(id)
                    )
                )
            );
    }

    updateComponent(componentBaseItem: ComponentBaseItem) {
        console.debug(componentBaseItem) // TODO
        this.componentHttpService
            .updateComponent(componentBaseItem)
            .subscribe(result => {
                console.debug(result); // TODO

                this.store.dispatch(putBaseItem(result));
            });
    }

    createComponent(componentRevision: ComponentBaseItem) {
        return this.componentHttpService.createComponent(componentRevision).pipe(
            tap(() => {
                this.store.dispatch(addBaseItem(componentRevision));
            })
        );
    }

    deleteComponent(componentId: string): Observable<ComponentBaseItem> {
        return this.componentHttpService.deleteComponent(componentId).pipe(
            tap(_ => {
                this.localStorageService.removeBaseItemFromLastOpened(componentId);
                this.store.dispatch(removeBaseItem(componentId));
            })
        );
    }

    testComponent(id: string, wiring: Wiring): Observable<ComponentBaseItem> {
        return of(null).pipe(
            tap(() => this.store.dispatch(setExecutionRunning())),
            switchMapTo(this.componentHttpService.executeComponent(id, wiring)),
            tap(result => this.store.dispatch(setExecutionProtocol(result))),
            finalize(() => this.store.dispatch(setExecutionFinished()))
        );
    }

    bindWiringToComponent(componentId: string, workflowWiring: Wiring) {
        return this.componentHttpService
            .bindWiringToComponent(componentId, workflowWiring)
            .pipe(
                tap(result => {
                    this.store.dispatch(putBaseItem(result));
                })
            );
    }

    private _patchComponentProperties(baseItemId: string) {
        return this.componentHttpService.getComponent(baseItemId).pipe(
            tap(componentBaseItem => {
                return this.store.dispatch(patchComponentProperties(componentBaseItem));
            })
        );
    }
}
