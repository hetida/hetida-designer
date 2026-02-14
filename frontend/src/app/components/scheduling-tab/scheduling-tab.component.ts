import { ComponentPortal } from '@angular/cdk/portal';
import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { Store } from '@ngrx/store';
import { lastValueFrom, Observable, of } from 'rxjs';
import { tap, finalize, switchMap, first } from 'rxjs/operators';
import { MatDialog } from '@angular/material/dialog';

import {
  // ConfirmClickEvent,
  ExecutionDialogData,
  WiringDialogComponent
} from 'hd-wiring';

import { TransformationHttpService } from '../../service/http-service/transformation-http.service';
import { Transformation } from 'src/app/model/transformation';
import { ContextMenuService } from 'src/app/service/context-menu/context-menu.service';
import { selectTransformationById } from 'src/app/store/transformation/transformation.selectors';
import { TransformationState } from 'src/app/store/transformation/transformation.state';
import { TabItemService } from '../../service/tab-item/tab-item.service';
import { TransformationContextMenuComponent } from '../transformation-context-menu/transformation-context-menu.component';
import { WiringConfigService } from 'src/app/app.module';
import { v4 as UUID } from 'uuid';
import {
  ConfirmDialogComponent,
  ConfirmDialogData,
  ConfirmDialogResult
} from '../confirmation-dialog/confirm-dialog.component';

interface Schedule {
  id: string;
  active: boolean;
  name: string;
  transformation_id: string;
  transformation_name: string;
  transformation_version_tag: string;
  transformation_state: TransformationState;
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
    private readonly wiringConfigService: WiringConfigService,
    private readonly transformationStore: Store<TransformationState>,
    private readonly transformationHttpService: TransformationHttpService,
    private readonly tabItemService: TabItemService,
    private readonly contextMenuService: ContextMenuService
  ) {}

  schedules: Schedule[] = [
    {
      id: '80d1abdb-efa7-4588-90cc-92a39cdabca0',
      name: 'Aggregation Bedarfsprognose Inputdaten',
      cron_expression: '*/6 * * * *',
      active: false,
      transformation_id: null,
      transformation_name: null,
      transformation_version_tag: null,
      transformation_state: null,
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
      transformation_state: null,
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
      transformation_state: null,
      wiring: null
    }
  ];

  editingCell: { scheduleId: number; field: keyof Schedule } | null = null;
  editValue = '';

  addNewSchedule(): void {
    const newRow: Schedule = {
      id: UUID().toString(),
      name: 'New Schedule',
      cron_expression: '0 0 * * *', // Default: daily at midnight
      active: false,
      transformation_id: null,
      transformation_name: null,
      transformation_version_tag: null,
      transformation_state: null,
      wiring: null
    };
    this.schedules.push(newRow);
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

  public async onDrop(event: DragEvent, schedule: Schedule): Promise<void> {
    event.preventDefault();

    const data = event.dataTransfer.getData('hetida/transformation');
    if (data) {
      try {
        const transformation = JSON.parse(data);
        schedule.transformation_id = transformation.id;
        schedule.transformation_name = transformation.name;
        schedule.transformation_version_tag = transformation.version_tag;
        schedule.transformation_state = transformation.state;
      } catch (e) {
        console.error('Failed to parse transformation data', e);
      }
    }

    await this.openWiringDialog(schedule);
  }

  edit(schedule: any) {
    schedule.original = {
      name: schedule.name,
      cronExpression: schedule.cronExpression
    };
    schedule.editing = true;
  }

  getScheduleTrafo(schedule: any): Observable<any> {
    return this.transformationStore
      .select(selectTransformationById(schedule.transformation_id))
      .pipe(first());
  }

  async openWiringDialog(schedule: Schedule): Promise<void> {
    const adapterList = await lastValueFrom(
      this.transformationHttpService.getAdapterList()
    );
    this.transformationStore
      .select(selectTransformationById(schedule.transformation_id))
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
              test_wiring: schedule.wiring,
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
              schedule.wiring = test_wiring;
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

  delete(schedule: Schedule): Observable<boolean> {
    const dialogRef = this.dialog.open<
      ConfirmDialogComponent,
      ConfirmDialogData,
      ConfirmDialogResult
    >(ConfirmDialogComponent, {
      width: '640px',
      data: {
        title: `Delete Schedule ${schedule.name}`,
        content: `Do you want to delete the schedule ${schedule.name} permanently?`,
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
          const index = this.schedules.findIndex(r => r.id === schedule.id);
          if (index !== -1) {
            this.schedules.splice(index, 1);
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

  startEdit(scheduleId: number, field: keyof Schedule, currentValue: string) {
    this.editingCell = { scheduleId, field };
    this.editValue = currentValue;
    // Focus after Angular renders the input
    setTimeout(() => {
      const input = document.querySelector<HTMLInputElement>('.cell-input');
      input?.focus();
      input?.select(); // select all text
    }, 0);
  }

  isEditing(scheduleId: number, field: keyof Schedule): boolean {
    return (
      this.editingCell?.scheduleId === scheduleId &&
      this.editingCell?.field === field
    );
  }

  saveEdit(schedule: Schedule) {
    if (this.editingCell) {
      const field = this.editingCell.field;
      // Type-safe assignment
      switch (field) {
        case 'name':
          schedule.name = this.editValue;
          break;
        case 'cron_expression':
          schedule.cron_expression = this.editValue;
          break;
        default:
          console.warn('Unexpected field');
          break;
      }
      // Here you would typically call your API
      console.warn('Saved:', schedule);

      this.cancelEdit();
    }
  }

  cancelEdit() {
    this.editingCell = null;
    this.editValue = '';
  }

  onKeyDown(event: KeyboardEvent, schedule: Schedule) {
    if (event.key === 'Enter') {
      this.saveEdit(schedule);
    } else if (event.key === 'Escape') {
      this.cancelEdit();
    }
  }

  ngOnInit() {
    console.warn('Should load schedules');
  }

  select(schedule: Schedule) {
    // open as tab?
    this.transformationStore
      .select(selectTransformationById(schedule.transformation_id))
      .pipe(first())
      .subscribe(transformation => {
        this.tabItemService.addTransformationTab(transformation.id);
      });
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
}
