import { Injectable } from '@angular/core';
import { Store } from '@ngrx/store';
import { EMPTY, forkJoin, Observable, of } from 'rxjs';
import {
  finalize,
  first,
  shareReplay,
  switchMap,
  switchMapTo,
  tap
} from 'rxjs/operators';
import { v4 as uuid } from 'uuid';
import { TransformationType } from '../../enums/transformation-type';
import { RevisionState } from '../../enums/revision-state';
import { IAppState } from '../../store/app.state';
import {
  ComponentTransformation,
  isFullTransformation,
  Transformation,
  TrafoUpdateState,
  WorkflowTransformation,
  UnitTestResults,
  UpdatedTransformation
} from '../../model/transformation';
import {
  TransformationHttpService,
  DeleteResult
} from '../http-service/transformation-http.service';
import {
  addTransformation,
  removeTransformation,
  setAllTransformations,
  updateTransformation
} from '../../store/transformation/transformation.actions';
import { selectTransformationById } from '../../store/transformation/transformation.selectors';
import { selectOrderedTabItems } from '../../store/tab-item/tab-item.selectors';
import { LocalStorageService } from '../local-storage/local-storage.service';
import { TestWiring } from 'hd-wiring';
import {
  setExecutionFinished,
  setExecutionProtocol,
  setExecutionRunning
} from 'src/app/store/execution-protocol/execution-protocol.actions';
import { ExecutionResponse } from '../../components/protocol-viewer/protocol-viewer.component';
import { Utils } from 'src/app/utils/utils';
import { NotificationService } from 'src/app/service/notifications/notification.service';

@Injectable({
  providedIn: 'root'
})
export class TransformationService {
  private readonly fullTransformationRequests = new Map<
    string,
    Observable<Transformation>
  >();

  constructor(
    private readonly transformationHttpService: TransformationHttpService,
    private readonly localStorageService: LocalStorageService,
    private readonly store: Store<IAppState>,
    private readonly notificationService: NotificationService
  ) {}

  createTransformation(transformation: Transformation): Observable<never> {
    return this.transformationHttpService
      .createTransformation(transformation)
      .pipe(
        first(),
        tap(result => {
          this.store.dispatch(addTransformation(result));
        }),
        switchMap(() => EMPTY)
      );
  }

  updateTransformation(
    transformation: Transformation
  ): Observable<UpdatedTransformation> {
    return this.transformationHttpService
      .updateTransformation(transformation)
      .pipe(
        tap(updatedTransformation => {
          if (
            updatedTransformation.update_state ===
            TrafoUpdateState.RESETTED_FROM_DB_BECAUSE_CHANGES_INTRODUCING_CYCLES_NOT_ALLOWED
          ) {
            this.notificationService.warn(
              'Workflow was resetted because changes introduced cycles.'
            );
          }
          if (
            updatedTransformation.update_state ===
            TrafoUpdateState.UNALLOWED_COMPONENT_IMPORTS
          ) {
            this.notificationService.warn(
              'Component was resetted because component imports do not obey rules, e.g. must be released for released component.'
            );
          }
          this.store.dispatch(updateTransformation(updatedTransformation));
        })
      );
  }

  upgradeWorkflowOperators(
    transformation: Transformation
  ): Observable<Transformation> {
    return this.transformationHttpService
      .upgradeWorkflowOperators(transformation)
      .pipe(
        tap(updatedTransformation => {
          if (
            updatedTransformation.update_state ===
            TrafoUpdateState.RESETTED_FROM_DB_BECAUSE_CHANGES_INTRODUCING_CYCLES_NOT_ALLOWED
          ) {
            this.notificationService.warn(
              'Workflow was resetted because changes introduced cycles.'
            );
          }
          this.store.dispatch(updateTransformation(updatedTransformation));
        })
      );
  }

  upgradeSingleOperator(
    transformation: Transformation,
    operatorId: string,
    newRevisionId: string
  ): Observable<Transformation> {
    return this.transformationHttpService
      .upgradeSingleOperator(transformation, operatorId, newRevisionId)
      .pipe(
        tap(updatedTransformation => {
          if (
            updatedTransformation.update_state ===
            TrafoUpdateState.RESETTED_FROM_DB_BECAUSE_CHANGES_INTRODUCING_CYCLES_NOT_ALLOWED
          ) {
            this.notificationService.warn(
              'Workflow was resetted because changes introduced cycles.'
            );
          }
          this.store.dispatch(updateTransformation(updatedTransformation));
        })
      );
  }

  updateExpandComponent(
    transformation: Transformation
  ): Observable<Transformation> {
    return this.transformationHttpService
      .updateExpandComponent(transformation)
      .pipe(
        tap(updatedTransformation => {
          this.store.dispatch(updateTransformation(updatedTransformation));
        })
      );
  }

  unitTestComponent(
    transformation: Transformation
  ): Observable<UnitTestResults> {
    return this.transformationHttpService.unitTestComponent(transformation);
  }

  importTrafoRevFromString(
    trafoRevsString: string,
    updateCode: boolean,
    expandCode: boolean,
    overwriteReleased: boolean
  ): Observable<Response> {
    return this.transformationHttpService.importTrafoRevFromString(
      trafoRevsString,
      updateCode,
      expandCode,
      overwriteReleased
    );
  }

  getDefaultComponentTransformation(): ComponentTransformation {
    return {
      id: uuid().toString(),
      revision_group_id: uuid().toString(),
      name: 'New component',
      category: 'Draft',
      type: TransformationType.COMPONENT,
      version_tag: '0.1.0',
      state: RevisionState.DRAFT,
      description: 'New created component',
      io_interface: {
        inputs: [],
        outputs: []
      },
      test_wiring: {
        input_wirings: [],
        output_wirings: []
      },
      content: ''
    };
  }

  getDefaultWorkflowTransformation(): WorkflowTransformation {
    return {
      id: uuid().toString(),
      revision_group_id: uuid().toString(),
      name: 'New Workflow',
      category: 'Draft',
      type: TransformationType.WORKFLOW,
      version_tag: '0.1.0',
      state: RevisionState.DRAFT,
      description: 'New created workflow',
      io_interface: {
        inputs: [],
        outputs: []
      },
      test_wiring: {
        input_wirings: [],
        output_wirings: []
      },
      content: {
        operators: [],
        links: [],
        inputs: [],
        outputs: [],
        constants: []
      }
    };
  }

  /**
   * Load all transformations as stubs into the store (see isFullTransformation).
   *
   * The transformations of open tabs are loaded fully in the same step, so that
   * their editors never see a stub when this is called again, e.g. after an import.
   */
  fetchAllTransformations(): void {
    this.store
      .select(selectOrderedTabItems)
      .pipe(
        first(),
        switchMap(tabItems => {
          const openTransformationIds = [
            ...new Set(
              tabItems
                .map(tabItem => tabItem.transformationId)
                .filter(id => Utils.isDefined(id))
            )
          ];
          return forkJoin([
            this.transformationHttpService.fetchTransformationStubs(),
            openTransformationIds.length > 0
              ? this.transformationHttpService.fetchTransformationsByIds(
                  openTransformationIds
                )
              : of<Transformation[]>([])
          ]);
        })
      )
      .subscribe(([stubs, fullTransformations]) => {
        const fullTransformationsById = new Map(
          fullTransformations.map(transformation => [
            transformation.id,
            transformation
          ])
        );
        this.store.dispatch(
          setAllTransformations(
            stubs.map(stub => fullTransformationsById.get(stub.id) ?? stub)
          )
        );
      });
  }

  /**
   * Get the full transformation (see isFullTransformation) with the given id:
   * from the store if it is fully loaded there, otherwise from the backend,
   * putting it into the store.
   */
  getFullTransformation(id: string): Observable<Transformation> {
    return this.store.select(selectTransformationById(id)).pipe(
      first(),
      switchMap(transformation =>
        isFullTransformation(transformation)
          ? of(transformation)
          : this.fetchFullTransformation(id)
      )
    );
  }

  /**
   * Return the given transformation itself if it is full, otherwise its full
   * version (see getFullTransformation). Returning the given object keeps changes
   * that are not in the store, e.g. of the workflow currently being edited.
   */
  ensureFullTransformation(
    transformation: Transformation
  ): Observable<Transformation> {
    return isFullTransformation(transformation)
      ? of(transformation)
      : this.getFullTransformation(transformation.id);
  }

  private fetchFullTransformation(id: string): Observable<Transformation> {
    // Share concurrent requests for the same transformation, e.g. when a tab is
    // opened while the context menu is still loading the transformation.
    let request = this.fullTransformationRequests.get(id);
    if (request === undefined) {
      request = this.transformationHttpService.fetchTransformation(id).pipe(
        tap(transformation =>
          this.store.dispatch(updateTransformation(transformation))
        ),
        finalize(() => this.fullTransformationRequests.delete(id)),
        shareReplay({ bufferSize: 1, refCount: true })
      );
      this.fullTransformationRequests.set(id, request);
    }
    return request;
  }

  deleteTransformation(id: string): Observable<DeleteResult> {
    return this.transformationHttpService.deleteTransformation(id).pipe(
      tap(result => {
        if (result.success) {
          this.localStorageService.removeItemFromLastOpened(id);
          this.store.dispatch(removeTransformation(id));
        } else {
          switch (result.status) {
            case 409: // Conflict
              this.notificationService.warn(
                'Could not delete. Transformation is probably in use in another workflow.'
              );
              break;
            case 404:
              this.notificationService.warn(
                'Could not delete. Cannot find Transformation.'
              );
              break;
            default:
              break;
          }
        }
      })
    );
  }

  // releaseTransformation and disableTransformation may be called with stubs
  // from the store, e.g. for the other revisions of a revision group.
  releaseTransformation(
    transformation: Transformation
  ): Observable<UpdatedTransformation> {
    return this.ensureFullTransformation(transformation).pipe(
      switchMap(fullTransformation => {
        const copyOfTransformation = Utils.deepCopy(fullTransformation);
        copyOfTransformation.state = RevisionState.RELEASED;
        copyOfTransformation.released_timestamp = new Date().toISOString();
        return this.updateTransformation(copyOfTransformation);
      })
    );
  }

  disableTransformation(
    transformation: Transformation
  ): Observable<Transformation> {
    return this.ensureFullTransformation(transformation).pipe(
      switchMap(fullTransformation => {
        const copyOfTransformation = Utils.deepCopy(fullTransformation);
        copyOfTransformation.state = RevisionState.DISABLED;
        copyOfTransformation.disabled_timestamp = new Date().toISOString();
        return this.updateTransformation(copyOfTransformation);
      })
    );
  }

  testTransformation(
    id: string,
    test_wiring: TestWiring
  ): Observable<ExecutionResponse> {
    return of(null).pipe(
      tap(() => this.store.dispatch(setExecutionRunning())),
      switchMapTo(
        this.transformationHttpService.executeTransformation(id, test_wiring)
      ),
      tap(result => {
        if (result !== null && result !== undefined) {
          this.store.dispatch(setExecutionProtocol(result));
        }
      }),
      finalize(() => this.store.dispatch(setExecutionFinished()))
    );
  }
}
