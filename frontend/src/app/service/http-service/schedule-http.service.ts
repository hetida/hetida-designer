import { Injectable } from '@angular/core';
import {
  HttpClient,
  HttpErrorResponse,
  HttpParams,
  HttpResponse
} from '@angular/common/http';
import { ConfigService } from '../configuration/config.service';
import { catchError, throwError, Observable, of, map } from 'rxjs';
import { Schedule } from '../../model/schedule';
import { NotificationService } from 'src/app/service/notifications/notification.service';
import { ScheduleExecution } from 'src/app/components/schedule-executions-dialog/schedule-executions-dialog.component';

export interface DeleteResult {
  success: boolean;
  status: number;
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ScheduleHttpService {
  private apiEndpoint: string;

  constructor(
    private readonly httpClient: HttpClient,
    private readonly config: ConfigService,
    private readonly notificationService: NotificationService
  ) {
    this.config.getConfig().subscribe(runtimeConfig => {
      this.apiEndpoint = runtimeConfig.apiEndpoint;
    });
  }

  public fetchSchedules(): Observable<Array<Schedule>> {
    const url = `${this.apiEndpoint}/schedules`;
    return this.httpClient.get<Array<Schedule>>(url);
  }

  public createSchedule(schedule: Schedule): Observable<Schedule> {
    const url = `${this.apiEndpoint}/schedules/`;
    return this.httpClient.post<Schedule>(url, schedule);
  }

  public updateSchedule(schedule: Schedule): Observable<Schedule> {
    const url = `${this.apiEndpoint}/schedules/${schedule.id}`;

    return this.httpClient.put<Schedule>(url, schedule).pipe(
      catchError((error: HttpErrorResponse) => {
        this.notificationService.error('Failed to update schedule!');

        // Re-throw the error so subscribers can still handle it if needed
        return throwError(() => error);
      })
    );
  }

  public deleteSchedule(id: string): Observable<DeleteResult> {
    const url = `${this.apiEndpoint}/schedules/${id}`;

    return this.httpClient.delete<void>(url, { observe: 'response' }).pipe(
      map((response: HttpResponse<void>) => ({
        success: true,
        status: response.status
      })),
      catchError((error: HttpErrorResponse) => {
        return of({
          success: false,
          status: error.status,
          error: error.message
        });
      })
    );
  }

  public fetchScheduleExecutions(
    scheduleId: string,
    exclude_exec_result: boolean,
    exclude_exec_input: boolean
  ): Observable<ScheduleExecution[]> {
    const params = new HttpParams()
      .set('schedule_id', scheduleId)
      .set('exclude_exec_result', exclude_exec_result)
      .set('exclude_exec_input', exclude_exec_input);

    const url = `${this.apiEndpoint}/schedules/executions`;

    return this.httpClient.get<ScheduleExecution[]>(url, { params });
  }

  public fetchScheduleExecution(
    scheduleExecutionId: string
  ): Observable<ScheduleExecution> {
    const url = `${this.apiEndpoint}/schedules/executions/${scheduleExecutionId}`;
    return this.httpClient.get<ScheduleExecution>(url);
  }
}
