import { ComponentPortal } from '@angular/cdk/portal';
import {
  Component,
  ElementRef,
  OnInit,
  ViewChild,
  OnDestroy
} from '@angular/core';
import { Store } from '@ngrx/store';
import { lastValueFrom, Observable, of, combineLatest, Subject } from 'rxjs';
import {
  tap,
  finalize,
  switchMap,
  first,
  map,
  takeUntil
} from 'rxjs/operators';
import { MatDialog } from '@angular/material/dialog';

import { ExecutionDialogData, WiringDialogComponent } from 'hd-wiring';

import { TransformationHttpService } from '../../service/http-service/transformation-http.service';
import { Transformation } from 'src/app/model/transformation';
import { ContextMenuService } from 'src/app/service/context-menu/context-menu.service';
import { selectTransformationById } from 'src/app/store/transformation/transformation.selectors';
import { TransformationState } from 'src/app/store/transformation/transformation.state';
import { TabItemService } from '../../service/tab-item/tab-item.service';
import { TransformationContextMenuComponent } from '../transformation-context-menu/transformation-context-menu.component';
import { WiringConfigService } from 'src/app/app.module';
import { v4 as UUID } from 'uuid';
import { Schedule } from '../../model/schedule';
import {
  ConfirmDialogComponent,
  ConfirmDialogData,
  ConfirmDialogResult
} from '../confirmation-dialog/confirm-dialog.component';
import { ScheduleHttpService } from '../../service/http-service/schedule-http.service';

@Component({
  selector: 'hd-scheduling-tab',
  templateUrl: './scheduling-tab.component.html',
  styleUrls: ['./scheduling-tab.component.scss']
})
export class SchedulingTabComponent implements OnInit, OnDestroy {
  @ViewChild('scheduleTableContainer') scheduleTableContainer: ElementRef;

  private readonly destroy$ = new Subject<void>();

  constructor(
    private readonly dialog: MatDialog,
    private readonly wiringConfigService: WiringConfigService,
    private readonly transformationStore: Store<TransformationState>,
    private readonly transformationHttpService: TransformationHttpService,
    private readonly scheduleHttpService: ScheduleHttpService,
    private readonly tabItemService: TabItemService,
    private readonly contextMenuService: ContextMenuService
  ) {}

  schedules: Schedule[] = [];
  isLoading = false;

  editingCell: { scheduleId: number; field: keyof Schedule } | null = null;
  editValue = '';

  ngOnInit() {
    this.loadSchedules();
  }

  private loadSchedules(): void {
    this.isLoading = true;
    this.scheduleHttpService
      .fetchSchedules()
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: schedules => {
          this.schedules = schedules;
          this.subscribeToTransformationUpdates();
        },
        error: err => console.error('Failed to load schedules:', err)
      });
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private updateScheduleInApi(schedule: Schedule): void {
    this.scheduleHttpService.updateSchedule(schedule).subscribe({
      next: updated_schedule => {
        schedule.cron_expression_valid = updated_schedule.cron_expression_valid;
      },
      error: err => console.error('Failed to update schedule:', err)
    });
  }

  private subscribeToTransformationUpdates(): void {
    const transformationObservables = this.schedules.map((schedule, index) => {
      if (!schedule.transformation_id) {
        return of({ schedule, transformation: null, index });
      }

      return this.transformationStore
        .select(selectTransformationById(schedule.transformation_id))
        .pipe(
          map(transformation => ({
            schedule,
            transformation,
            index
          }))
        );
    });

    combineLatest(transformationObservables)
      .pipe(takeUntil(this.destroy$))
      .subscribe(results => {
        results.forEach(({ schedule, transformation, index }) => {
          if (transformation) {
            this.schedules[index].transformation_name = transformation.name;
            this.schedules[index].transformation_version_tag =
              transformation.version_tag;
            this.schedules[index].transformation_state = transformation.state;

            this.updateScheduleInApi(this.schedules[index]);
          } else if (schedule.transformation_id) {
            this.schedules[index].transformation_id = null;
            this.schedules[index].transformation_name = null;
            this.schedules[index].transformation_version_tag = null;
            this.schedules[index].transformation_state = null;

            this.updateScheduleInApi(this.schedules[index]);
          }
        });
      });
  }

  private refreshTransformationSubscriptions(): void {
    this.destroy$.next();
    this.subscribeToTransformationUpdates();
  }

  addNewSchedule(): void {
    const schedule: Schedule = {
      id: UUID().toString(),
      name: 'New Schedule',
      cron_expression: '*/5 * * * *',
      active: false,
      transformation_id: null,
      transformation_name: null,
      transformation_version_tag: null,
      transformation_state: null,
      wiring: {},
      cron_expression_valid: null
    };

    this.scheduleHttpService.createSchedule(schedule).subscribe({
      next: createdSchedule => {
        this.schedules.push(createdSchedule);
        this.refreshTransformationSubscriptions();
        setTimeout(() => {
          if (this.scheduleTableContainer) {
            const element = this.scheduleTableContainer.nativeElement;
            element.scrollTop = element.scrollHeight;
          }
        }, 0);
      },
      error: err => console.error('Failed to create schedule:', err)
    });
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

        this.refreshTransformationSubscriptions();

        this.updateScheduleInApi(schedule);
      } catch (e) {
        console.error('Failed to parse transformation data', e);
      }
    }

    await this.openWiringDialog(schedule);
  }

  getScheduleTrafo(schedule: Schedule): Observable<Transformation> {
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
              this.updateScheduleInApi(schedule);
            }),
            finalize(() => dialogRef.close())
          )
          .subscribe();

        dialogRef.afterClosed().subscribe(() => {
          this.wiringConfigService.resetToDefaults();
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
          return this.scheduleHttpService.deleteSchedule(schedule.id).pipe(
            map(deleteResult => {
              if (deleteResult.success) {
                const index = this.schedules.findIndex(
                  r => r.id === schedule.id
                );
                if (index !== -1) {
                  this.schedules.splice(index, 1);
                  this.refreshTransformationSubscriptions();
                }
              } else {
                console.error('Failed to delete schedule:', deleteResult.error);
              }
              return deleteResult.success;
            })
          );
        }
        return of(result?.confirmed);
      })
    );
  }

  startEdit(scheduleId: number, field: keyof Schedule, currentValue: string) {
    this.editingCell = { scheduleId, field };
    this.editValue = currentValue;
    // Focus after Angular renders the input
    setTimeout(() => {
      const input = document.querySelector<HTMLInputElement>('.cell-input');
      input?.focus();
      input?.select(); // select all existing text
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
          console.error('Unexpected field');
          break;
      }

      this.updateScheduleInApi(schedule);

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

  onActiveToggleChange(schedule: Schedule): void {
    this.updateScheduleInApi(schedule);
  }

  openTrafoOfScheduleInTab(schedule: Schedule) {
    this.transformationStore
      .select(selectTransformationById(schedule.transformation_id))
      .pipe(first())
      .subscribe(transformation => {
        this.tabItemService.addTransformationTab(transformation.id);
      });
  }

  openTransformationContextMenu(schedule: Schedule, mouseEvent: MouseEvent) {
    const { componentPortalRef } = this.contextMenuService.openContextMenu(
      new ComponentPortal(TransformationContextMenuComponent),
      {
        x: mouseEvent.clientX,
        y: mouseEvent.clientY
      }
    );

    this.getScheduleTrafo(schedule).subscribe(trafo => {
      componentPortalRef.instance.transformation = trafo;
    });
  }

  run(schedule: Schedule) {
    // TODO: Implement manual run functionality
    console.warn('Running schedule:', schedule);
  }
}
