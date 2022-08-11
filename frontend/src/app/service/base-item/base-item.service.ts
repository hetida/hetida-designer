import { Injectable } from '@angular/core';
import { Store } from '@ngrx/store';
import { EMPTY, Observable } from 'rxjs';
import { first, switchMap, tap } from 'rxjs/operators';
import { v4 as uuid } from 'uuid';
import { BaseItemType } from '../../enums/base-item-type';
import { RevisionState } from '../../enums/revision-state';
import { ComponentBaseItem } from '../../model/component-base-item';
import { WorkflowBaseItem } from '../../model/workflow-base-item';
import { IAppState } from '../../store/app.state';
import { getBaseItems } from '../../store/base-item/base-item.actions';
import { BaseItemHttpService } from '../http-service/base-item-http.service';
import {
  ComponentTransformation,
  Transformation
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

@Injectable({
  providedIn: 'root'
})
export class BaseItemService {
  constructor(
    private readonly transformationHttpService: TransformationHttpService,
    private readonly transformationStore: Store<TransformationState>,
    private readonly localStorageService: LocalStorageService,
    private readonly baseItemHttpService: BaseItemHttpService,
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

  updateTransformation(transformation: Transformation): void {
    this.transformationHttpService
      .updateTransformation(transformation)
      .subscribe(updatedTransformation => {
        this.transformationStore.dispatch(
          updateTransformation(updatedTransformation)
        );
      });
  }

  createWorkflow(): WorkflowBaseItem {
    const workflowId = uuid().toString();
    return {
      id: workflowId,
      groupId: uuid().toString(),
      name: 'New workflow',
      category: 'Draft',
      type: BaseItemType.WORKFLOW,
      tag: '1.0.0',
      state: RevisionState.DRAFT,
      description: 'New created workflow',
      inputs: [],
      outputs: [],
      wirings: [],
      links: [],
      operators: []
    };
  }

  createComponent(): ComponentBaseItem {
    const componentId = uuid().toString();
    return {
      id: componentId,
      groupId: uuid().toString(),
      name: 'New component',
      category: 'Draft',
      type: BaseItemType.COMPONENT,
      tag: '1.0.0',
      state: RevisionState.DRAFT,
      description: 'New created component',
      inputs: [],
      outputs: [],
      wirings: [],
      code: ''
    };
  }

  getDefaultComponentTransformation(): ComponentTransformation {
    return {
      id: uuid().toString(),
      revision_group_id: uuid().toString(),
      name: 'New component',
      category: 'Draft',
      type: BaseItemType.COMPONENT,
      version_tag: '1.0.0',
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

  fetchAllTransformations(): void {
    // TODO remove once everything is migrated to transformations
    this.baseItemHttpService.fetchBaseItems().subscribe(result => {
      this.store.dispatch(getBaseItems(result));
    });
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
  releaseTransformation(transformation: Transformation): void {
    // TODO copy, do not change param attribute
    transformation.state = RevisionState.RELEASED;
    transformation.released_timestamp = new Date().toISOString();
    this.updateTransformation(transformation);
  }

  disableTransformation(transformation: Transformation): void {
    transformation.state = RevisionState.DISABLED;
    transformation.disabled_timestamp = new Date().toISOString();
    this.updateTransformation(transformation);
  }
}
