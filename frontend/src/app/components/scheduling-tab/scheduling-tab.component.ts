import { ComponentPortal } from '@angular/cdk/portal';
import {
  Component,
  ElementRef,
  OnInit,
  ViewChild,
  OnDestroy
} from '@angular/core';
import { Store } from '@ngrx/store';
import { Observable, of, combineLatest, Subject, EMPTY } from 'rxjs';
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
import {
  selectTransformationById,
  selectTransformationsLoaded
} from 'src/app/store/transformation/transformation.selectors';
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
import { TransformationService } from 'src/app/service/transformation/transformation.service';
import { NotificationService } from 'src/app/service/notifications/notification.service';
import {
  ScheduleExecutionsDialogComponent,
  ScheduleExecutionsDialogData
} from '../schedule-executions-dialog/schedule-executions-dialog.component';
@Component({
  selector: 'hd-scheduling-tab',
  templateUrl: './scheduling-tab.component.html',
  styleUrls: ['./scheduling-tab.component.scss'],
  standalone: false
})
export class SchedulingTabComponent implements OnInit, OnDestroy {
  @ViewChild('scheduleTableContainer') scheduleTableContainer: ElementRef;

  private readonly destroy$ = new Subject<void>();
  private readonly transformationSub$ = new Subject<void>();

  constructor(
    private readonly dialog: MatDialog,
    private readonly wiringConfigService: WiringConfigService,
    private readonly transformationService: TransformationService,
    private readonly transformationStore: Store<TransformationState>,
    private readonly transformationHttpService: TransformationHttpService,
    private readonly scheduleHttpService: ScheduleHttpService,
    private readonly tabItemService: TabItemService,
    private readonly contextMenuService: ContextMenuService,
    private readonly notificationService: NotificationService
  ) {}

  schedules: Schedule[] = [];
  isLoading = false;

  editingCell: { scheduleId: string; field: keyof Schedule } | null = null;
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
    this.transformationSub$.next();
    this.transformationSub$.complete();
  }

  trackById(_index: number, schedule: Schedule): string {
    return schedule.id;
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
        .pipe(map(transformation => ({ schedule, transformation, index })));
    });

    combineLatest([
      combineLatest(transformationObservables),
      this.transformationStore.select(selectTransformationsLoaded)
    ])
      .pipe(takeUntil(this.transformationSub$))
      .subscribe(([results, transformationsLoaded]) => {
        results.forEach(({ schedule, transformation }) => {
          if (transformation) {
            // initially the trafo detail information on the schedule object may be null
            // since the backend does not provide it. So if unset, we initialize it from
            // the trafo store transformation object
            schedule.transformation_name ??= transformation.name;
            schedule.transformation_version_tag ??= transformation.version_tag;
            schedule.transformation_state ??= transformation.state;
            schedule.transformation_type ??= transformation.type;

            // only now it makes sense to check if changes occured
            // otherwise the initial assignement would trigger a change
            // and would lead sending an update request for every schedule
            // to the backend at first loading of the frontend!

            const changed =
              transformation?.name !== schedule.transformation_name ||
              transformation?.version_tag !==
                schedule.transformation_version_tag ||
              transformation?.state !== schedule.transformation_state ||
              transformation?.type !== schedule.transformation_type;

            if (changed) {
              schedule.transformation_name = transformation.name;
              schedule.transformation_version_tag = transformation.version_tag;
              schedule.transformation_state = transformation.state;
              schedule.transformation_type = transformation.type;
              this.updateScheduleInApi(schedule);
            }
          } else if (
            (transformation === null ||
              transformation === undefined ||
              schedule.transformation_id === null) &&
            transformationsLoaded
          ) {
            schedule.transformation_id = null;
            schedule.transformation_name = null;
            schedule.transformation_version_tag = null;
            schedule.transformation_state = null;
            schedule.transformation_type = null;
            this.updateScheduleInApi(schedule);
          }
        });
      });
  }

  private refreshTransformationSubscriptions(): void {
    this.transformationSub$.next();
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
      transformation_type: null,
      wiring: { input_wirings: [], output_wirings: [] },
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

  public onDrop(event: DragEvent, schedule: Schedule): void {
    event.preventDefault();

    const data = event.dataTransfer.getData('hetida/transformation');
    if (data) {
      try {
        const transformation = JSON.parse(data);
        schedule.transformation_id = transformation.id;
        schedule.transformation_name = transformation.name;
        schedule.transformation_version_tag = transformation.version_tag;
        schedule.transformation_state = transformation.state;
        schedule.transformation_type = transformation.type;

        this.refreshTransformationSubscriptions();

        this.updateScheduleInApi(schedule);
      } catch (e) {
        console.error('Failed to parse transformation data', e);
      }
    }

    this.openWiringDialog(schedule);
  }

  private getScheduleTrafo(schedule: Schedule): Observable<Transformation> {
    return this.transformationStore
      .select(selectTransformationById(schedule.transformation_id))
      .pipe(first());
  }

  openWiringDialog(schedule: Schedule): void {
    combineLatest([
      this.transformationHttpService.getAdapterList(),
      this.transformationStore
        .select(selectTransformationById(schedule.transformation_id))
        .pipe(first())
    ])
      .pipe(
        switchMap(([adapterList, transformation]) => {
          if (!transformation) {
            return EMPTY;
          }

          const dialogRef = this.dialog.open<
            WiringDialogComponent,
            ExecutionDialogData,
            never
          >(WiringDialogComponent, {
            data: {
              title: 'Change Wiring —',
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

          this.wiringConfigService.confirmationButtonText = 'Save Wiring';

          dialogRef.componentInstance.cancelDialogClick.subscribe(() =>
            dialogRef.close()
          );

          return dialogRef.componentInstance.confirmClick.pipe(
            first(), // complete after first confirmation click
            tap(({ test_wiring }) => {
              schedule.wiring = test_wiring;
              this.updateScheduleInApi(schedule);
              dialogRef.close();
            }),
            finalize(() => {
              this.wiringConfigService.resetToDefaults();
            })
          );
        })
      )
      .pipe(takeUntil(this.destroy$))
      .subscribe();
  }

  delete(schedule: Schedule): void {
    this.dialog
      .open<ConfirmDialogComponent, ConfirmDialogData, ConfirmDialogResult>(
        ConfirmDialogComponent,
        {
          width: '640px',
          data: {
            title: `Delete Schedule ${schedule.name}`,
            content: `Do you want to delete the schedule ${schedule.name} permanently?`,
            actionOk: 'Delete Schedule',
            actionCancel: 'Cancel'
          }
        }
      )
      .afterClosed()
      .pipe(
        switchMap((result: ConfirmDialogResult | undefined) => {
          if (result?.confirmed) {
            return this.scheduleHttpService.deleteSchedule(schedule.id).pipe(
              tap(deleteResult => {
                if (deleteResult.success) {
                  const index = this.schedules.findIndex(
                    r => r.id === schedule.id
                  );
                  if (index !== -1) {
                    this.schedules.splice(index, 1);
                    this.refreshTransformationSubscriptions();
                  }
                } else {
                  console.error(
                    'Failed to delete schedule:',
                    deleteResult.error
                  );
                }
              })
            );
          }
          return of(void 0);
        })
      )
      .subscribe();
  }

  startEdit(scheduleId: string, field: keyof Schedule, currentValue: string) {
    this.editingCell = { scheduleId, field };
    this.editValue = currentValue;

    setTimeout(() => {
      const input = document.querySelector<HTMLInputElement>('.cell-input');
      input?.focus();
      input?.select(); // select all text
    }, 0);
  }

  isEditing(scheduleId: string, field: keyof Schedule): boolean {
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
    if (
      schedule.transformation_id === null ||
      schedule.wiring === null ||
      (schedule.wiring.input_wirings.length === 0 &&
        schedule.wiring.output_wirings.length === 0)
    ) {
      this.notificationService.warn(
        'Incomplete configuration. Cannot execute. Please check wiring!'
      );
      return;
    }
    this.transformationService
      .testTransformation(schedule.transformation_id, schedule.wiring)
      .subscribe();
  }

  openExecutionsDialog(schedule: Schedule): void {
    this.dialog.open<
      ScheduleExecutionsDialogComponent,
      ScheduleExecutionsDialogData
    >(ScheduleExecutionsDialogComponent, {
      width: '100%',
      height: '80vh',
      maxHeight: '80vh',
      data: { schedule }
    });
  }
}
