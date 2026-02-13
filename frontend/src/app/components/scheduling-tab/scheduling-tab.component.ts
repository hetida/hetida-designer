import { ComponentPortal } from '@angular/cdk/portal';
import { HttpClient } from '@angular/common/http';
import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { Store } from '@ngrx/store';
import { combineLatest, lastValueFrom, Observable, of } from 'rxjs';
import { map, tap, finalize, switchMap, first } from 'rxjs/operators';
import { MatDialog } from '@angular/material/dialog';
import {
  // ConfirmClickEvent,
  ExecutionDialogData,
  WiringDialogComponent,
  TestWiring
} from 'hd-wiring';

import { TransformationHttpService } from '../../service/http-service/transformation-http.service';
import { TransformationType } from 'src/app/enums/transformation-type';
import { Transformation } from 'src/app/model/transformation';
import { TransformationActionService } from 'src/app/service/transformation/transformation-action.service';
import { ConfigService } from '../../service/configuration/config.service';
import { ContextMenuService } from 'src/app/service/context-menu/context-menu.service';
import { LocalStorageService } from 'src/app/service/local-storage/local-storage.service';
import {
  selectHashedTransformationLookupById,
  selectTransformationById
} from 'src/app/store/transformation/transformation.selectors';
import { TransformationState } from 'src/app/store/transformation/transformation.state';
import { Utils } from 'src/app/utils/utils';
import { TabItemService } from '../../service/tab-item/tab-item.service';
import { TransformationContextMenuComponent } from '../transformation-context-menu/transformation-context-menu.component';
import { WiringConfigService } from 'src/app/app.module';
import { v4 as UUID } from 'uuid';
import {
  ConfirmDialogComponent,
  ConfirmDialogData,
  ConfirmDialogResult
} from '../confirmation-dialog/confirm-dialog.component';

interface DataRow {
  id: string;
  active: boolean;
  name: string;
  transformation_id: string;
  transformation_name: string;
  transformation_version_tag: string;
  cron_expression: string;
  wiring: any;
}

@Component({
  selector: 'hd-scheduling-tab',
  templateUrl: './scheduling-tab.component.html',
  styleUrls: ['./scheduling-tab.component.scss']
})
export class SchedulingTabComponent implements OnInit {
  @ViewChild('scheduleTableContainer') scheduleTableContainer: ElementRef;

  constructor(
    private readonly dialog: MatDialog,
    private readonly localStorageService: LocalStorageService,
    private readonly wiringConfigService: WiringConfigService,
    private readonly transformationStore: Store<TransformationState>,
    private readonly transformationHttpService: TransformationHttpService,
    private readonly transformationActionService: TransformationActionService,
    private readonly tabItemService: TabItemService,
    private readonly contextMenuService: ContextMenuService,
    private readonly httpClient: HttpClient,
    private readonly configService: ConfigService
  ) {}

  data: DataRow[] = [
    {
      id: '80d1abdb-efa7-4588-90cc-92a39cdabca0',
      name: 'Aggregation Bedarfsprognose Inputdaten',
      cron_expression: '*/6 * * * *',
      active: false,
      transformation_id: null,
      transformation_name: null,
      transformation_version_tag: null,
      wiring: null
    },
    {
      id: '2d48ce98-6ea0-4865-8bd9-908838f65920',
      name: 'Wasserbedarfsprognose Inferenz',
      cron_expression: '*/6 * * * *',
      active: true,
      transformation_id: '3c5916b0-00cc-4dc7-a45a-205fd0cdf412',
      transformation_name: 'Some Trafo',
      transformation_version_tag: '1.0.0',
      wiring: null
    },
    {
      id: '767287af-9788-474d-8b12-0ed8ea5883b5',
      name: 'Optimierung',
      cron_expression: '*/6 * * * *',
      active: true,
      transformation_id: null,
      transformation_name: null,
      transformation_version_tag: null,
      wiring: null
    }
  ];

  editingCell: { rowId: number; field: keyof DataRow } | null = null;
  editValue = '';

  public lastOpened: Observable<Transformation[]>;
  public version: string;
  public _userInfoText: string;

  public schedules = [
    {
      id: 42,
      name: 53,
      description: 'some job',
      transformation_id: null,
      transformation_name: 'some',
      transformation_version_tag: '1.0.0',
      active: true,
      cron_expression: '*/2 * * * *',
      wiring: { input_wirings: [], output_wirings: [] } as TestWiring
    },
    {
      id: 43,
      name: 54,
      description: 'another job',
      transformation_id: 'abcd1235',
      transformation_name: 'some other',
      transformation_version_tag: '1.1.0',
      active: true,
      cron_expression: '0 8 * * *',
      wiring: { input_wirings: [], output_wirings: [] } as TestWiring
    }
  ];

  addNewRow(): void {
    const newRow: DataRow = {
      id: UUID().toString(),
      name: 'New Schedule',
      cron_expression: '0 0 * * *', // Default: daily at midnight
      active: false,
      transformation_id: null,
      transformation_name: null,
      transformation_version_tag: null,
      wiring: null
    };
    this.data.push(newRow);
    setTimeout(() => {
      if (this.scheduleTableContainer) {
        const element = this.scheduleTableContainer.nativeElement;
        element.scrollTop = element.scrollHeight;
      }
    }, 0);
  }

  public onDragOver(event: DragEvent): void {
    event.preventDefault();

    event.dataTransfer.dropEffect = 'copy';
  }

  public async onDrop(event: DragEvent, row: DataRow): Promise<void> {
    event.preventDefault();

    const data = event.dataTransfer.getData('hetida/transformation');
    if (data) {
      try {
        const transformation = JSON.parse(data);
        row.transformation_id = transformation.id;
        row.transformation_name = transformation.name;
        row.transformation_version_tag = transformation.version_tag;
      } catch (e) {
        console.error('Failed to parse transformation data', e);
      }
    }

    await this.openWiringDialog(row);
  }

  edit(schedule: any) {
    schedule.original = {
      name: schedule.name,
      cronExpression: schedule.cronExpression
    };
    schedule.editing = true;
  }

  async openWiringDialog(row: DataRow): Promise<void> {
    const adapterList = await lastValueFrom(
      this.transformationHttpService.getAdapterList()
    );
    this.transformationStore
      .select(selectTransformationById(row.transformation_id))
      .pipe(first())
      .subscribe(transformation => {
        if (!transformation) {
          return;
          // Do nothing if transformation is null/undefined (no trafo could be found for this uuid)
        }

        const dialogTitle = 'Change Wiring —';

        this.wiringConfigService.confirmationButtonText = 'Save Wiring';

        const dialogRef = this.dialog.open<
          WiringDialogComponent,
          ExecutionDialogData,
          never
        >(WiringDialogComponent, {
          data: {
            title: dialogTitle,
            wiringItem: {
              name: transformation.name,
              test_wiring: row.wiring,
              id: transformation.id,
              version_tag: transformation.version_tag,
              io_interface: transformation.io_interface
            },
            adapterList
          }
        });

        dialogRef.componentInstance.cancelDialogClick.subscribe(() => {
          dialogRef.close();
        });

        dialogRef.componentInstance.confirmClick
          .pipe(
            tap(() => dialogRef.close()),

            tap(({ test_wiring }) => {
              row.wiring = test_wiring;
            }),
            finalize(() => dialogRef.close())
          )
          .subscribe();

        dialogRef.afterClosed().subscribe(result => {
          console.warn(result);
          this.wiringConfigService.resetToDefaults();
          // Handle any result from the dialog
        });
      });
  }

  delete(row: DataRow): Observable<boolean> {
    const dialogRef = this.dialog.open<
      ConfirmDialogComponent,
      ConfirmDialogData,
      ConfirmDialogResult
    >(ConfirmDialogComponent, {
      width: '640px',
      data: {
        title: `Delete Schedule ${row.name}`,
        content: `Do you want to delete the schedule ${row.name} permanently?`,
        actionOk: 'Delete Schedule',
        actionCancel: 'Cancel'
      }
    });

    return dialogRef.afterClosed().pipe(
      switchMap(result => {
        if (result?.confirmed) {
          // TODO: actually delete via API
          console.warn('Should delete');
          // Delete from current list of schedules
          const index = this.data.findIndex(r => r.id === row.id);
          if (index !== -1) {
            this.data.splice(index, 1);
          }
        }
        return of(result?.confirmed);
      })
    );
  }

  save(schedule: any) {
    schedule.editing = false;

    // TODO: call API here
    console.warn('Saved:', schedule);
  }

  cancel(schedule: any) {
    schedule.name = schedule.original.name;
    schedule.cronExpression = schedule.original.cronExpression;
    schedule.editing = false;
  }

  startEdit(rowId: number, field: keyof DataRow, currentValue: string) {
    this.editingCell = { rowId, field };
    this.editValue = currentValue;
    // Focus after Angular renders the input
    setTimeout(() => {
      const input = document.querySelector<HTMLInputElement>('.cell-input');
      input?.focus();
      input?.select(); // select all text
    }, 0);
  }

  isEditing(rowId: number, field: keyof DataRow): boolean {
    return (
      this.editingCell?.rowId === rowId && this.editingCell?.field === field
    );
  }

  saveEdit(row: DataRow) {
    if (this.editingCell) {
      const field = this.editingCell.field;
      // Type-safe assignment
      switch (field) {
        case 'name':
          row.name = this.editValue;
          break;
        case 'cron_expression':
          row.cron_expression = this.editValue;
          break;
        default:
          console.warn('Unexpected field');
          break;
      }
      // Here you would typically call your API
      console.warn('Saved:', row);

      this.cancelEdit();
    }
  }

  cancelEdit() {
    this.editingCell = null;
    this.editValue = '';
  }

  onKeyDown(event: KeyboardEvent, row: DataRow) {
    if (event.key === 'Enter') {
      this.saveEdit(row);
    } else if (event.key === 'Escape') {
      this.cancelEdit();
    }
  }

  ngOnInit() {
    this.httpClient
      .get<string>('assets/VERSION', { responseType: 'text' as 'json' })
      .subscribe((version: string) => {
        this.version = version;
      });
    this.lastOpened = combineLatest([
      this.localStorageService.notifier,
      this.transformationStore.select(selectHashedTransformationLookupById)
    ]).pipe(
      map(([_, transformationsLookup]) => {
        const lastOpenedTransformationIds: string[] =
          this.localStorageService.getItem('last-opened') ?? [];

        return lastOpenedTransformationIds
          .filter(() => !Utils.object.isEmpty(transformationsLookup))
          .map(transformationId => transformationsLookup[transformationId])
          .filter((transformation): transformation is Transformation =>
            Utils.isDefined(transformation)
          );
      })
    );
    this.configService.getConfig().subscribe(config => {
      this._userInfoText = config.userInfoText;
    });
  }

  get lastOpenedWorkflows() {
    return this.lastOpened.pipe(
      map(transformations => {
        return transformations.filter(
          transformation => transformation.type === TransformationType.WORKFLOW
        );
      })
    );
  }

  get lastOpenedComponents() {
    return this.lastOpened.pipe(
      map(transformations => {
        return transformations.filter(
          transformation => transformation.type === TransformationType.COMPONENT
        );
      })
    );
  }

  select(selectedItem: Transformation) {
    this.tabItemService.addTransformationTab(selectedItem.id);
  }

  openTransformationContextMenu(
    selectedItem: Transformation,
    mouseEvent: MouseEvent
  ) {
    const { componentPortalRef } = this.contextMenuService.openContextMenu(
      new ComponentPortal(TransformationContextMenuComponent),
      {
        x: mouseEvent.clientX,
        y: mouseEvent.clientY
      }
    );

    componentPortalRef.instance.transformation = selectedItem;
  }

  newWorkflow(): void {
    this.transformationActionService.newWorkflow();
  }

  newComponent(): void {
    this.transformationActionService.newComponent();
  }
}
