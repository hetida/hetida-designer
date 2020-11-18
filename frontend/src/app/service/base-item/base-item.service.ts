import { Injectable } from '@angular/core';
import { Store } from '@ngrx/store';
import { EMPTY, Observable, of } from 'rxjs';
import { first, switchMap, tap } from 'rxjs/operators';
import { v4 as uuid } from 'uuid';
import { BaseItemType } from '../../enums/base-item-type';
import { RevisionState } from '../../enums/revision-state';
import { AbstractBaseItem, BaseItem } from '../../model/base-item';
import { ComponentBaseItem } from '../../model/component-base-item';
import { WorkflowBaseItem } from '../../model/workflow-base-item';
import { IAppState } from '../../store/app.state';
import {
  isBaseItem,
  isComponentBaseItem,
  isWorkflowBaseItem
} from '../../store/base-item/base-item-guards';
import {
  addBaseItem,
  getBaseItems,
  putBaseItem
} from '../../store/base-item/base-item.actions';
import { selectAbstractBaseItemById } from '../../store/base-item/base-item.selectors';
import { ComponentEditorService } from '../component-editor.service';
import { BaseItemHttpService } from '../http-service/base-item-http.service';
import { WorkflowEditorService } from '../workflow-editor.service';

@Injectable({
  providedIn: 'root'
})
export class BaseItemService {
  constructor(
    private readonly baseItemHttpService: BaseItemHttpService,
    private readonly store: Store<IAppState>,
    private readonly workflowService: WorkflowEditorService,
    private readonly componentService: ComponentEditorService
  ) {}

  createBaseItem(abstractBaseItem: AbstractBaseItem): Observable<never> {
    return this.baseItemHttpService.createBaseItem(abstractBaseItem).pipe(
      first(),
      tap(result => {
        this.store.dispatch(addBaseItem(result));
      }),
      switchMap(() => EMPTY)
    );
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

  getBaseItem(baseItemId: string): Observable<BaseItem> {
    return this.store.select(selectAbstractBaseItemById(baseItemId)).pipe(
      switchMap(
        (abstractBaseItem: AbstractBaseItem): Observable<BaseItem> => {
          if (isBaseItem(abstractBaseItem)) {
            return of(abstractBaseItem);
          }

          return abstractBaseItem.type === BaseItemType.COMPONENT
            ? this.componentService.getComponent(abstractBaseItem.id)
            : this.workflowService.getWorkflow(abstractBaseItem.id);
        }
      )
    );
  }

  ensureBaseItem(baseItemId: string): Observable<never> {
    return this.getBaseItem(baseItemId).pipe(
      first(),
      switchMap(() => EMPTY)
    );
  }

  fetchBaseItems(): void {
    this.baseItemHttpService.fetchBaseItems().subscribe(result => {
      this.store.dispatch(getBaseItems(result));
    });
  }

  saveBaseItem(abstractBaseItem: AbstractBaseItem): void {
    this.baseItemHttpService
      .updateBaseItem(abstractBaseItem)
      .subscribe(result => {
        this.store.dispatch(putBaseItem(result));
      });
  }

  disableBaseItem(abstractBaseItem: AbstractBaseItem): void {
    abstractBaseItem.state = RevisionState.DISABLED;
    this.saveBaseItem(abstractBaseItem);
  }

  releaseBaseItem(baseItem: BaseItem): void {
    baseItem.state = RevisionState.RELEASED;
    if (isWorkflowBaseItem(baseItem)) {
      this.workflowService.updateWorkflow(baseItem);
    } else if (isComponentBaseItem(baseItem)) {
      this.componentService.updateComponent(baseItem);
    } else {
      throw Error(
        'base item is neither a workflow base item nor a component base item'
      );
    }
  }
}
