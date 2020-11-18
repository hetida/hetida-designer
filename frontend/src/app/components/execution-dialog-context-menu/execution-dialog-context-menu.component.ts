import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Inject,
  OnInit,
  Output
} from '@angular/core';
import { MatCheckboxChange } from '@angular/material/checkbox';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { AdapterUiFlatNode } from 'src/app/model/adapter-ui-node';
import { Utils } from 'src/app/utils/utils';
import { UiItemWiring } from '../execution-dialog/execution-dialog.component';

export interface WiringChangeEvent {
  ioItemId: string;
  checked: boolean;
}

export interface ExecutionContextMenuData {
  dataOrigin: AdapterUiFlatNode;
  IOItem: UiItemWiring[];
}

@Component({
  selector: 'hd-execution-dialog-context-menu',
  templateUrl: './execution-dialog-context-menu.component.html',
  styleUrls: ['./execution-dialog-context-menu.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ExecutionDialogContextMenuComponent implements OnInit {
  public executionContextData: ExecutionContextMenuData;

  public assignedUiItems: UiItemWiring[];

  @Output()
  public wiringChange = new EventEmitter<WiringChangeEvent>();

  constructor(@Inject(MAT_DIALOG_DATA) public data: ExecutionContextMenuData) {}

  ngOnInit() {
    this.executionContextData = this.data;
    this.assignedUiItems = this.data.IOItem.filter(d => this.hasOtherWiring(d));
  }

  isChecked(item: UiItemWiring): boolean {
    return Utils.isDefined(item.nodeId);
  }

  incompatibleTypes(item: UiItemWiring): boolean {
    if (typeof this.executionContextData.dataOrigin.dataType === 'string') {
      // is a series datatype
      if (
        item.dataType.toUpperCase().includes('SERIES') &&
        this.executionContextData.dataOrigin.dataType
          .toUpperCase()
          .includes('SERIES')
      ) {
        return false;
      }

      return (
        item.dataType.toUpperCase() !==
        this.executionContextData.dataOrigin.dataType.toUpperCase()
      );
    }
    return true;
  }

  public getTypeColor(type: string): string {
    return `var(--${type}-color)`;
  }

  itemSelectionChange(checkBoxChange: MatCheckboxChange, ioItem: UiItemWiring) {
    this.wiringChange.emit({
      ioItemId: ioItem.ioItemId,
      checked: checkBoxChange.checked
    });
  }

  hasOtherWiring(ioItem: UiItemWiring) {
    if (ioItem.nodeId === undefined || ioItem.nodeId === null) {
      return false;
    }

    return ioItem.nodeId !== this.data.dataOrigin.id;
  }
}
