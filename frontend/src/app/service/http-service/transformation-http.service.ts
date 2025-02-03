import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { ConfigService } from '../configuration/config.service';
import { Observable } from 'rxjs';
import { Transformation, UnitTestResults } from '../../model/transformation';
import { Adapter, TestWiring } from 'hd-wiring';
import { ExecutionResponse } from '../../components/protocol-viewer/protocol-viewer.component';

type TrafoStringMixed = Transformation | string;
@Injectable({
  providedIn: 'root'
})
export class TransformationHttpService {
  private apiEndpoint: string;

  constructor(
    private readonly httpClient: HttpClient,
    private readonly config: ConfigService
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
  ): Observable<Transformation> {
    const url = `${this.apiEndpoint}/transformations/${transformation.id}`;
    return this.httpClient.put<Transformation>(url, transformation);
  }

  public updateExpandComponent(
    transformation: Transformation
  ): Observable<Transformation> {
    const url = `${this.apiEndpoint}/transformations/${transformation.id}?update_component_code=true&expand_component_code=true`;
    return this.httpClient.put<Transformation>(url, transformation);
  }

  public unitTestComponent(
    transformation: Transformation
  ): Observable<UnitTestResults> {
    const url = `${this.apiEndpoint}/transformations/${transformation.id}/test`;
    return this.httpClient.post<UnitTestResults>(url, {});
  }

  public importTrafoRevFromString(
    trafo_revs_str: string,
    updateCode: boolean,
    expandCode: boolean,
    overwriteReleased: boolean
  ): Observable<Response> {
    let import_obj: TrafoStringMixed[];

    try {
      const parsed_json = JSON.parse(trafo_revs_str) as Transformation;

      if (Array.isArray(parsed_json)) {
        import_obj = parsed_json;
      } else {
        import_obj = [parsed_json];
      }
    } catch (error) {
      console.warn('Failed to parse Trafo(s) JSON:', error);
      import_obj = [trafo_revs_str];
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

    const url = `${this.apiEndpoint}/transformations/?update_component_code=true&expand_component_code=true`;
    return this.httpClient.put<Response>(url, import_obj, { params });
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
