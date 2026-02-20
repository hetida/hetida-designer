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

  /**
   * Update schedule in the API
   * This method is called whenever a schedule is modified, either by:
   * - User editing fields (name, cron_expression)
   * - User toggling active state
   * - User changing transformation assignment
   * - Underlying transformation being updated in the store
   */
  private updateScheduleInApi(schedule: Schedule): void {
    this.scheduleHttpService.updateSchedule(schedule).subscribe({
      next: updated_schedule => {
        schedule.cron_expression_valid = updated_schedule.cron_expression_valid;
      },
      error: err => console.error('Failed to update schedule:', err)
    });
  }

  /**
   * Subscribe to transformation updates from the store for all schedules
   * that have a transformation_id set
   */
  private subscribeToTransformationUpdates(): void {
    // Create an array of observables for each schedule's transformation
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

    // Combine all observables and update schedules when any transformation changes
    combineLatest(transformationObservables)
      .pipe(takeUntil(this.destroy$))
      .subscribe(results => {
        results.forEach(({ schedule, transformation, index }) => {
          if (transformation) {
            // Update schedule with latest transformation data
            this.schedules[index].transformation_name = transformation.name;
            this.schedules[index].transformation_version_tag =
              transformation.version_tag;
            this.schedules[index].transformation_state = transformation.state;

            // Update schedule in API when transformation changes
            this.updateScheduleInApi(this.schedules[index]);
          } else if (schedule.transformation_id) {
            // Transformation was deleted or not found
            this.schedules[index].transformation_id = null;
            this.schedules[index].transformation_name = null;
            this.schedules[index].transformation_version_tag = null;
            this.schedules[index].transformation_state = null;

            // Update schedule in API when transformation is marked as disabled
            this.updateScheduleInApi(this.schedules[index]);
          }
        });
      });
  }

  /**
   * Re-subscribe to transformation updates after schedule changes
   * Call this after adding/removing schedules or changing transformation_id
   */
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
        // Use the server-returned schedule (it may have a server-assigned id)
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

        // Refresh subscriptions to track the newly assigned transformation
        this.refreshTransformationSubscriptions();

        // Update schedule in API when transformation is assigned
        this.updateScheduleInApi(schedule);
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
              // Update schedule in API when wiring is changed
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

      // Update schedule in API after user edits
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
    // Update schedule in API when active state is toggled
    this.updateScheduleInApi(schedule);
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

  run(schedule: Schedule) {
    // TODO: Implement run functionality
    console.warn('Running schedule:', schedule);
  }
}
