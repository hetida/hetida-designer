import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Inject,
  Output
} from '@angular/core';
import { MatCheckboxChange } from '@angular/material/checkbox';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { IOType } from 'hetida-flowchart';
import { AdapterHttpService } from '../adapter-http.service';
import { TreeNodeWithUiInfo } from '../node-click/node-click';
import { Utils } from '../utils/utils';
import { UiItemWiring } from '../wiring-dialog';

export interface WiringChangeEvent {
  ioItemId: string;
  checked: boolean;
}

export interface ExecutionContextMenuData {
  dataOrigin: TreeNodeWithUiInfo;
  IOItem: UiItemWiring[];
}

@Component({
  selector: 'hd-execution-dialog-context-menu',
  templateUrl: './node-wiring-context-menu.component.html',
  styleUrls: ['./node-wiring-context-menu.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false
})
export class NodeWiringContextMenuComponent {
  @Output()
  public wiringChange = new EventEmitter<WiringChangeEvent>();

  constructor(
    @Inject(MAT_DIALOG_DATA)
    public executionContextData: ExecutionContextMenuData
  ) {}

  isChecked(item: UiItemWiring): boolean {
    return (
      Utils.isDefined(item.nodeId) &&
      item.nodeId === this.executionContextData.dataOrigin.id
    );
  }

  isAssigned(item: UiItemWiring): boolean {
    return Utils.isDefined(item.nodeId);
  }

  incompatibleTypes(item: UiItemWiring): boolean {
    if (Utils.isDefined(this.executionContextData.dataOrigin.type)) {
      return AdapterHttpService.isIncompatibleWithIoType(
        this.executionContextData.dataOrigin.type,
        item.ioType
      );
    }
    return true;
  }

  public getTypeColor(ioType: IOType): string {
    return `var(--${ioType}-color)`;
  }

  itemSelectionChange(
    checkBoxChange: MatCheckboxChange,
    ioItem: UiItemWiring
  ): void {
    this.wiringChange.emit({
      ioItemId: ioItem.ioItemId,
      checked: checkBoxChange.checked
    });
  }
}
