import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ConfigService } from './../configuration/config.service';
import { InputWiring, OutputWiring } from './wiring-http.service';

export interface AdapterList {
  id: number;
  name: string;
}

export interface AdapterResponse {
  id: number;
  name: string;
  thingNodes: ThingNodes[];
  sources: DataSourceSink[];
  sinks: DataSourceSink[];
}

export interface ThingNodes {
  id: string;
  name: string;
  parentId: string | null;
}

export interface DataSourceSink {
  id: string;
  name: string;
  thingNodeId: string;
  dataType: string;
  filters?: DataSourceSinkDateRangeFilter | {} | null | undefined;
}

interface DataSourceSinkDateRangeFilter {
  fromTimestamp: DateRangeFilterDetail;
  toTimestamp: DateRangeFilterDetail;
}

interface DateRangeFilterDetail {
  name: string;
  dataType: any;
  required: boolean;
  min: string;
  max: string;
}

@Injectable({
  providedIn: 'root'
})
export class AdapterHttpService {
  private apiEndpoint: string;

  constructor(
    private readonly http: HttpClient,
    private readonly config: ConfigService
  ) {
    this.config.getConfig().subscribe(runtimeConfig => {
      this.apiEndpoint = runtimeConfig.apiEndpoint;
    });
  }

  public static isDateFilter(
    value: any
  ): value is DataSourceSinkDateRangeFilter {
    return value && 'fromTimestamp' in value && 'toTimestamp' in value;
  }

  public static isOutputWiring(value: any): value is OutputWiring {
    return 'sinkId' in (value as OutputWiring);
  }

  public static isInputWiring(value: any): value is InputWiring {
    return 'sourceId' in (value as InputWiring);
  }

  public getAdapter(): Observable<AdapterList[]> {
    const url = `${this.apiEndpoint}/adapters/`;
    return this.http.get<AdapterList[]>(url);
  }

  public getOneAdapter(id: number): Observable<AdapterResponse> {
    const url = `${this.apiEndpoint}/adapters/${id}/metadata`;
    return this.http.get<AdapterResponse>(url);
  }
}
