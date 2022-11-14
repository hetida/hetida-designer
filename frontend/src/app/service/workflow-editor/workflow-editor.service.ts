import { Injectable } from '@angular/core';
import { Store } from '@ngrx/store';
import { TestWiring } from 'hd-wiring';
import { iif, Observable, of } from 'rxjs';
import { finalize, switchMap, switchMapTo, tap } from 'rxjs/operators';
import { WorkflowBaseItem } from '../../model/workflow-base-item';
import { IAppState } from '../../store/app.state';
import { isWorkflowBaseItem } from '../../store/base-item/base-item-guards';
import {
  addBaseItem,
  patchWorkflowProperties,
  putBaseItem,
  removeBaseItem
} from '../../store/base-item/base-item.actions';
import {
  selectAbstractBaseItemById,
  selectWorkflowBaseItemById
} from '../../store/base-item/base-item.selectors';
import {
  setExecutionFinished,
  setExecutionProtocol,
  setExecutionRunning
} from '../../store/execution-protocol/execution-protocol.actions';
import { WorkflowHttpService } from '../http-service/workflow-http.service';
import { LocalStorageService } from '../local-storage/local-storage.service';

@Injectable({
  providedIn: 'root'
})
export class WorkflowEditorService {
  constructor(
    private readonly workflowHttpService: WorkflowHttpService,
    private readonly store: Store<IAppState>,
    private readonly localStorageService: LocalStorageService
  ) {}

  getWorkflow(id: string): Observable<WorkflowBaseItem> {
    return this.store.select(selectAbstractBaseItemById(id)).pipe(
      switchMap(baseItem =>
        // check if we already have the workflow loaded, if yes and force is false do nothing, otherwise load workflow and put into store
        iif(
          () => isWorkflowBaseItem(baseItem),
          this.store.select(selectWorkflowBaseItemById(id)),
          this._patchWorkflowProperties(id)
        )
      )
    );
  }

  updateWorkflow(workflowRevision: WorkflowBaseItem) {
    this.workflowHttpService
      .updateWorkflow(workflowRevision)
      .subscribe(result => {
        this.store.dispatch(putBaseItem(result));
      });
  }

  deleteWorkflow(workflowId: string): Observable<WorkflowBaseItem> {
    return this.workflowHttpService.deleteWorkflow(workflowId).pipe(
      tap(() => {
        this.localStorageService.removeItemFromLastOpened(workflowId);
        this.store.dispatch(removeBaseItem(workflowId));
      })
    );
  }

  createWorkflow(workflowRevision: WorkflowBaseItem) {
    return this.workflowHttpService.createWorkflow(workflowRevision).pipe(
      tap(() => {
        this.store.dispatch(addBaseItem(workflowRevision));
      })
    );
  }

  bindWiringToWorkflow(workflowId: string, wiring: TestWiring) {
    return this.workflowHttpService
      .bindWiringToWorkflow(workflowId, wiring)
      .pipe(
        tap(result => {
          this.store.dispatch(putBaseItem(result));
        })
      );
  }

  testWorkflow(id: string, wiring: TestWiring): Observable<WorkflowBaseItem> {
    return of(null).pipe(
      tap(() => this.store.dispatch(setExecutionRunning())),
      switchMapTo(this.workflowHttpService.executeWorkflow(id, wiring)),
      tap(result => this.store.dispatch(setExecutionProtocol(result))),
      finalize(() => this.store.dispatch(setExecutionFinished()))
    );
  }

  private _patchWorkflowProperties(
    baseItemId: string
  ): Observable<WorkflowBaseItem> {
    return this.workflowHttpService.getWorkflow(baseItemId).pipe(
      tap(workflowBaseItem => {
        this.store.dispatch(patchWorkflowProperties(workflowBaseItem));
      })
    );
  }
}
