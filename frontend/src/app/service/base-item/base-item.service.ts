import { Injectable } from '@angular/core';
import { Store } from '@ngrx/store';
import { EMPTY, Observable, of } from 'rxjs';
import { finalize, first, switchMap, switchMapTo, tap } from 'rxjs/operators';
import { v4 as uuid } from 'uuid';
import { BaseItemType } from '../../enums/base-item-type';
import { RevisionState } from '../../enums/revision-state';
import { IAppState } from '../../store/app.state';
import {
  ComponentTransformation,
  Transformation,
  WorkflowTransformation
} from '../../model/new-api/transformation';
import { TransformationHttpService } from '../http-service/transformation-http.service';
import {
  addTransformation,
  removeTransformation,
  setAllTransformations,
  updateTransformation
} from '../../store/transformation/transformation.actions';
import { TransformationState } from '../../store/transformation/transformation.state';
import { LocalStorageService } from '../local-storage/local-storage.service';
import { TestWiring } from 'hd-wiring';
import {
  setExecutionFinished,
  setExecutionProtocol,
  setExecutionRunning
} from 'src/app/store/execution-protocol/execution-protocol.actions';
import { ExecutionResponse } from '../../components/protocol-viewer/protocol-viewer.component';
import { Utils } from 'src/app/utils/utils';

@Injectable({
  providedIn: 'root'
})
export class BaseItemService {
  constructor(
    private readonly transformationHttpService: TransformationHttpService,
    private readonly transformationStore: Store<TransformationState>,
    private readonly localStorageService: LocalStorageService,
    private readonly store: Store<IAppState>
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
  ): Observable<Transformation> {
    return this.transformationHttpService
      .updateTransformation(transformation)
      .pipe(
        tap(updatedTransformation => {
          this.transformationStore.dispatch(
            updateTransformation(updatedTransformation)
          );
        })
      );
  }

  getDefaultComponentTransformation(): ComponentTransformation {
    return {
      id: uuid().toString(),
      revision_group_id: uuid().toString(),
      name: 'New component',
      category: 'Draft',
      type: BaseItemType.COMPONENT,
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
      type: BaseItemType.WORKFLOW,
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

  fetchAllTransformations(): void {
    this.transformationHttpService
      .fetchTransformations()
      .subscribe(transformations => {
        this.transformationStore.dispatch(
          setAllTransformations(transformations)
        );
      });
  }

  deleteTransformation(id: string): Observable<void> {
    return this.transformationHttpService.deleteTransformation(id).pipe(
      tap(_ => {
        this.localStorageService.removeItemFromLastOpened(id);
        this.store.dispatch(removeTransformation(id));
      })
    );
  }

  // TODO unit test
  releaseTransformation(
    transformation: Transformation
  ): Observable<Transformation> {
    const copyOfTransformation = Utils.deepCopy(transformation);
    copyOfTransformation.state = RevisionState.RELEASED;
    copyOfTransformation.released_timestamp = new Date().toISOString();
    return this.updateTransformation(copyOfTransformation);
  }

  disableTransformation(
    transformation: Transformation
  ): Observable<Transformation> {
    const copyOfTransformation = Utils.deepCopy(transformation);
    copyOfTransformation.state = RevisionState.DISABLED;
    copyOfTransformation.disabled_timestamp = new Date().toISOString();
    return this.updateTransformation(copyOfTransformation);
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
      tap(result => this.store.dispatch(setExecutionProtocol(result))),
      finalize(() => this.store.dispatch(setExecutionFinished()))
    );
  }
}
