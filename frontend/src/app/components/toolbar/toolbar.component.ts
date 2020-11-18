import { Component, Input, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { NgHetidaFlowchartService } from 'ng-hetida-flowchart';
import { timer } from 'rxjs';
import { filter, switchMap } from 'rxjs/operators';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { RevisionState } from 'src/app/enums/revision-state';
import { BaseItem } from 'src/app/model/base-item';
import { BaseItemActionService } from 'src/app/service/base-item/base-item-action.service';
import { IAppState } from 'src/app/store/app.state';
import { selectBaseItemById } from 'src/app/store/base-item/base-item.selectors';

@Component({
  selector: 'hd-toolbar',
  templateUrl: './toolbar.component.html',
  styleUrls: ['./toolbar.component.scss']
})
export class ToolbarComponent implements OnInit {
  constructor(
    private readonly store: Store<IAppState>,
    private readonly flowchartService: NgHetidaFlowchartService,
    private readonly baseItemAction: BaseItemActionService
  ) {}

  @Input() baseItemId: string;

  baseItem: BaseItem;

  get isWorkflow(): boolean {
    return this.baseItem.type === BaseItemType.WORKFLOW;
  }

  get baseItemHasEmptyInputsAndOutputs(): boolean {
    return (
      this.baseItem.inputs.length === 0 && this.baseItem.outputs.length === 0
    );
  }

  incompleteFlag = false;

  ngOnInit() {
    timer(0, 100)
      .pipe(switchMap(() => this.baseItemAction.isIncomplete(this.baseItem)))
      .subscribe(isIncomplete => {
        this.incompleteFlag = isIncomplete;
      });
    this.store
      .pipe(
        select(
          selectBaseItemById(this.baseItemId),
          filter(baseItem => baseItem !== undefined)
        )
      )
      .subscribe(baseItem => (this.baseItem = baseItem));
  }

  zoomIn() {
    this.flowchartService.zoomIn(this.baseItem.id);
  }

  zoomOut() {
    this.flowchartService.zoomOut(this.baseItem.id);
  }

  showWorkflow() {
    this.flowchartService.showEntireWorkflow(this.baseItem.id);
  }

  showDocumentation() {
    this.baseItemAction.showDocumentation(this.baseItem);
  }

  async execute() {
    await this.baseItemAction.execute(this.baseItem);
  }

  get publishTooltip(): string {
    if (!this.isReleased()) {
      return 'Publish';
    }
    return 'Already published';
  }

  async publish(): Promise<void> {
    await this.baseItemAction.publish(this.baseItem);
  }

  configureIO() {
    this.baseItemAction.configureIO(this.baseItem);
    this.baseItemAction.isIncomplete(this.baseItem).then(b => {
      this.incompleteFlag = b;
    });
  }

  get deprecateTooltip(): string {
    if (!this.isReleased()) {
      return `Deprecate is disabled, because the ${this.baseItem.type.toLowerCase()} is not released.`;
    }
    return 'Deprecate';
  }

  deprecate(): void {
    this.baseItemAction.deprecate(this.baseItem);
  }

  async copy() {
    await this.baseItemAction.copy(this.baseItem);
  }

  get newRevisionTooltip(): string {
    if (!this.isReleased()) {
      return `New revision is disabled, because the ${this.baseItem.type.toLowerCase()} is not released.`;
    }
    return 'New revision';
  }

  async newRevision() {
    await this.baseItemAction.newRevision(this.baseItem);
  }

  isReleased() {
    return this.baseItem.state === RevisionState.RELEASED;
  }

  get executeTooltip(): string {
    if (this.incompleteFlag === true) {
      return `Cannot execute, because the ${this.baseItem.type.toLowerCase()} is incomplete.`;
    }
    return 'Execute';
  }

  get deleteTooltip(): string {
    if (this.isReleased()) {
      return `Cannot delete this ${this.baseItem.type.toLowerCase()}, because it is already released`;
    }
    return 'Delete';
  }

  delete() {
    this.baseItemAction.delete(this.baseItem);
  }

  editDetails(): void {
    this.baseItemAction.editDetails(this.baseItem);
  }
}
