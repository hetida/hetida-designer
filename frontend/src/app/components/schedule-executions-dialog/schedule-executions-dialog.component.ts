import { Component, Inject, OnDestroy, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { finalize, takeUntil } from 'rxjs/operators';
import { ScheduleHttpService } from '../../service/http-service/schedule-http.service';
import { Schedule } from '../../model/schedule';
import { IAppState } from '../../store/app.state';
import { Store } from '@ngrx/store';
import { setExecutionProtocol } from 'src/app/store/execution-protocol/execution-protocol.actions';
import { ExecutionResponse } from '../../components/protocol-viewer/protocol-viewer.component';
import { TextResultDialogService } from 'src/app/service/text-result-service/text-result-dialog.service';
import { TestWiring } from 'hd-wiring';
import { Subject } from 'rxjs';

export type ScheduledJobState =
  | 'STARTED'
  | 'INVOCATION_ERROR'
  | 'EXECUTION_ERROR'
  | 'SKIPPED'
  | 'SUCCESS';

export interface ScheduleExecution {
  id: string;
  schedule_id: string;
  transformation_id: string;
  transformation_name: string | null;
  transformation_version_tag: string | null;
  transformation_type: string | null;
  transformation_state: string | null;
  trafo_exec_job_id: string;
  state: ScheduledJobState;
  start: string | null;
  end: string | null;
  last_state_update: string | null;
  error_message: string | null;
  exec_input: ExecByIdInput | null;
  exec_result: ExecutionResponse | null;
}

export interface ExecByIdInput {
  id: string;
  wiring: TestWiring;
  run_pure_plot_operators: boolean;
}

export interface ScheduleExecutionsDialogData {
  schedule: Schedule;
}

@Component({
  selector: 'hd-schedule-executions-dialog',
  templateUrl: './schedule-executions-dialog.component.html',
  styleUrls: ['./schedule-executions-dialog.component.scss']
})
export class ScheduleExecutionsDialogComponent implements OnInit, OnDestroy {
  executions: ScheduleExecution[] = [];
  isLoading = false;
  errorMessage: string | null = null;
  readonly localTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  private readonly destroy$ = new Subject<void>();

  displayedColumns: string[] = [
    'last_state_update',
    'start',
    //'end',
    'trafo',
    'duration',
    'state',
    'exec_input',
    'exec_result',
    'error_message'
  ];

  constructor(
    private readonly dialogRef: MatDialogRef<ScheduleExecutionsDialogComponent>,
    private readonly scheduleHttpService: ScheduleHttpService,
    private readonly store: Store<IAppState>,
    private readonly resultDialogService: TextResultDialogService,

    @Inject(MAT_DIALOG_DATA) public data: ScheduleExecutionsDialogData
  ) {}

  ngOnInit(): void {
    this.loadExecutions();
  }

  loadExecutions(): void {
    this.isLoading = true;
    this.errorMessage = null;
    this.scheduleHttpService
      // exlude exec_result and exec_input, since these objects may be large. When these
      // should be shown explicitely, the execution will be fetched fully.
      .fetchScheduleExecutions(this.data.schedule.id, true, true)
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: executions => {
          this.executions = executions.slice().sort((a, b) => {
            const aTime = a.last_state_update
              ? new Date(a.last_state_update).getTime()
              : 0;
            const bTime = b.last_state_update
              ? new Date(b.last_state_update).getTime()
              : 0;
            return bTime - aTime;
          });
        },
        error: err => {
          console.error('Failed to load executions:', err);
          this.errorMessage = 'Failed to load executions. Please try again.';
        }
      });
  }

  getDuration(execution: ScheduleExecution): string {
    if (!execution.start || !execution.end) {
      return '—';
    }
    const ms =
      new Date(execution.end).getTime() - new Date(execution.start).getTime();
    if (ms < 1000) {
      return `${ms}ms`;
    }
    const seconds = Math.floor(ms / 1000);
    if (seconds < 60) {
      return `${seconds}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  }

  getTrafoName(name: string): string {
    // during execution hd runtime wraps components in workflows and
    // the name in the execution result has this in its name.
    // As we want to show the original name, we unwrap the name string.
    const match = name?.match(/^WF-WRAPPED\s*\(id=[^)]+\)\s*(.*)/);
    return match ? match[1] : name;
  }

  onShowExecResult(execution: ScheduleExecution): void {
    // need to fetch full schedule execution including exec_result
    this.scheduleHttpService
      .fetchScheduleExecution(execution.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: full_execution => {
          this.store.dispatch(setExecutionProtocol(full_execution.exec_result));
          this.close();
        },
        error: err => {
          console.error('Failed to load execution:', err);
        }
      });
  }

  onShowExecInput(execution: ScheduleExecution): void {
    // need to fetch full schedule execution which includes exec_input
    this.scheduleHttpService.fetchScheduleExecution(execution.id).subscribe({
      next: full_execution => {
        const formattedJson = JSON.stringify(
          full_execution.exec_input,
          null,
          2
        );
        this.resultDialogService.openDialog(
          'Execution Input',
          formattedJson,
          '800px'
        );
      },
      error: err => {
        console.error('Failed to load execution:', err);
      }
    });
  }

  close(): void {
    this.dialogRef.close();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
