import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Inject,
  OnInit,
  Output
} from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatSelectChange } from '@angular/material/select';
import { IOType } from 'hetida-flowchart';
import {
  AdapterHttpService,
  MetaData,
  PrimitiveDataType
} from '../adapter-http.service';
import { TreeNodeWithUiInfo } from '../node-click/node-click';
import { Utils } from '../utils/utils';
import { UiItemWiring } from '../wiring-dialog/wiring-dialog.component';

export interface MetaDataWiringChangeEvent {
  metaData?: MetaData;
  ioItemId: string;
}

export interface MetadataWiringModalData {
  nodeOrigin: TreeNodeWithUiInfo;
  IoItemWiring: UiItemWiring[];
  metaDataList: MetaData[];
}

@Component({
  selector: 'hd-meta-data-wiring-modal',
  templateUrl: './meta-data-wiring-modal.component.html',
  styleUrls: ['./meta-data-wiring-modal.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false
})
export class MetaDataWiringModalComponent implements OnInit {
  @Output()
  metaDataWiringChange = new EventEmitter<MetaDataWiringChangeEvent>();

  constructor(
    @Inject(MAT_DIALOG_DATA) public _metaDataDialogData: MetadataWiringModalData
  ) {}

  ngOnInit(): void {}

  _incompatibleTypes(item: UiItemWiring, metaData: MetaData): boolean {
    return AdapterHttpService.isIncompatibleWithIoType(
      metaData.dataType,
      item.ioType
    );
  }

  _isWiredToAnOtherNode(
    currentIoItemWiring: UiItemWiring,
    metaData: MetaData
  ): boolean {
    const otherWiring = !!this._metaDataDialogData.IoItemWiring.filter(
      ioItemWiring => ioItemWiring.ioItemName !== currentIoItemWiring.ioItemName
    ).find(ioItemWiring => ioItemWiring.metaDataKey === metaData.key);
    return otherWiring;
  }

  _notWiredUiItems(): UiItemWiring[] {
    return this._metaDataDialogData.IoItemWiring.filter(ioItem => {
      return (
        Utils.isNullOrUndefined(ioItem.nodeId) ||
        ioItem.nodeId === this._metaDataDialogData.nodeOrigin.id
      );
    });
  }

  _wiredMetaDataKey(uiItemWiring: UiItemWiring): string | null {
    if (uiItemWiring.nodeId === this._metaDataDialogData.nodeOrigin.id) {
      return uiItemWiring.metaDataKey ?? null;
    }
    return null;
  }

  _getMetaDataName(uiItemWiring: UiItemWiring): string {
    const metaDataKey = this._wiredMetaDataKey(uiItemWiring);
    return (
      this._metaDataDialogData.metaDataList.find(
        metaData => metaData.key === metaDataKey
      )?.key ?? ''
    );
  }

  _wireToUiItem(
    uiItemWiring: UiItemWiring,
    matSelectChange: MatSelectChange
  ): void {
    const metaDataToBind = this._metaDataDialogData.metaDataList.find(
      metaData => metaData.key === matSelectChange.value
    );
    this.metaDataWiringChange.emit({
      metaData: metaDataToBind,
      ioItemId: uiItemWiring.ioItemId
    });
  }

  _getTypeColor(type: IOType): string {
    return `var(--${type}-color)`;
  }

  _getIoTypeOfAdapterType(adapterType: PrimitiveDataType): IOType {
    return AdapterHttpService.getIOTypeFromAdapterType(adapterType);
  }
}
