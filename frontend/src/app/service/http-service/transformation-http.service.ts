import { Injectable } from '@angular/core';
import {
  HttpClient,
  HttpParams,
  HttpErrorResponse
} from '@angular/common/http';
import { ConfigService } from '../configuration/config.service';
import { catchError, throwError, Observable } from 'rxjs';
import {
  Transformation,
  UpdatedTransformation,
  UnitTestResults
} from '../../model/transformation';
import { Adapter, TestWiring } from 'hd-wiring';
import { ExecutionResponse } from '../../components/protocol-viewer/protocol-viewer.component';
import { NotificationService } from 'src/app/service/notifications/notification.service';

type TrafoStringMixed = Transformation | string;
@Injectable({
  providedIn: 'root'
})
export class TransformationHttpService {
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

  public fetchTransformations(): Observable<Array<Transformation>> {
    const url = `${this.apiEndpoint}/transformations`;
    return this.httpClient.get<Array<Transformation>>(url);
  }

  public createTransformation(
    transformation: Transformation
  ): Observable<Transformation> {
    const url = `${this.apiEndpoint}/transformations/`;
    return this.httpClient.post<Transformation>(url, transformation);
  }

  public updateTransformation(
    transformation: Transformation
  ): Observable<UpdatedTransformation> {
    const url = `${this.apiEndpoint}/transformations/${transformation.id}`;
    return this.httpClient.put<UpdatedTransformation>(url, transformation).pipe(
      catchError((error: HttpErrorResponse) => {
        this.notificationService.error('Failed to update transformation!');

        // Re-throw the error so subscribers can still handle it if needed
        return throwError(() => error);
      })
    );
  }

  public upgradeWorkflowOperators(
    transformation: Transformation
  ): Observable<UpdatedTransformation> {
    const url = `${this.apiEndpoint}/transformations/${transformation.id}/upgrade_operators`;
    return this.httpClient.put<UpdatedTransformation>(url, transformation);
  }

  public upgradeSingleOperator(
    transformation: Transformation,
    operatorId: string,
    newRevisionId: string
  ): Observable<UpdatedTransformation> {
    let params = new HttpParams();
    params = params.append(
      'new_operator_transformation_revision_id',
      newRevisionId
    );
    const url = `${this.apiEndpoint}/transformations/${transformation.id}/upgrade_operators/${operatorId}`;
    return this.httpClient.put<UpdatedTransformation>(url, transformation, {
      params
    });
  }

  public updateExpandComponent(
    transformation: Transformation
  ): Observable<Transformation> {
    let params = new HttpParams();

    params = params.append('update_component_code', 'true');
    params = params.append('expand_component_code', 'true');

    const url = `${this.apiEndpoint}/transformations/${transformation.id}`;
    return this.httpClient.put<Transformation>(url, transformation, { params });
  }

  public unitTestComponent(
    transformation: Transformation
  ): Observable<UnitTestResults> {
    const url = `${this.apiEndpoint}/transformations/${transformation.id}/test`;
    return this.httpClient.post<UnitTestResults>(url, {});
  }

  public importTrafoRevFromString(
    trafoRevisionsString: string,
    updateCode: boolean,
    expandCode: boolean,
    overwriteReleased: boolean
  ): Observable<Response> {
    let importObj: TrafoStringMixed[];
    try {
      const parsedJson = JSON.parse(trafoRevisionsString) as Transformation;

      if (Array.isArray(parsedJson)) {
        importObj = parsedJson;
      } else {
        importObj = [parsedJson];
      }
    } catch (error) {
      console.warn('Failed to parse Trafo(s) JSON:', error);
      importObj = [trafoRevisionsString];
    }

    let params = new HttpParams();

    if (updateCode) {
      params = params.append('update_component_code', 'true');
    }
    if (expandCode) {
      params = params.append('expand_component_code', 'true');
    }
    if (overwriteReleased) {
      params = params.append('allow_overwrite_released', 'true');
    }

    const url = `${this.apiEndpoint}/transformations/`;
    return this.httpClient.put<Response>(url, importObj, { params });
  }

  public deleteTransformation(id: string): Observable<void> {
    const url = `${this.apiEndpoint}/transformations/${id}`;
    // eslint-disable-next-line
    return this.httpClient.delete<void>(url);
  }

  public executeTransformation(
    id: string,
    wiring: TestWiring
  ): Observable<ExecutionResponse> {
    const url = `${this.apiEndpoint}/transformations/execute`;
    const body = { id, wiring, run_pure_plot_operators: true };

    return this.httpClient.post<ExecutionResponse>(url, body);
  }

  public getAdapterList(): Observable<Adapter[]> {
    const url = `${this.apiEndpoint}/adapters/`;
    return this.httpClient.get<Adapter[]>(url);
  }
}
