import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { IOType } from 'hetida-flowchart';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Utils } from './utils/utils';

/**
 * WIRING INTERFACES
 */
export type NodeSourceType = 'SOURCE' | 'SINK' | 'THINGNODE';

export interface WiringDateRangeFilter {
  value?: string;
  timestampTo?: string;
  timestampFrom?: string;
}

type FreeTextFilters = Partial<Record<string, string>>;

export type InputFilters = WiringDateRangeFilter & FreeTextFilters;

export interface InputWiring {
  workflow_input_name: string;
  adapter_id: string;
  ref_id?: string;
  ref_id_type?: NodeSourceType;
  ref_key?: string;
  type?: AdapterDataType;
  filters?: InputFilters | null | undefined;
  use_default_value?: boolean;
}

export interface OutputWiring {
  workflow_output_name: string;
  adapter_id: string;
  ref_id?: string;
  ref_id_type?: NodeSourceType;
  ref_key?: string;
  type?: AdapterDataType;
  filters?: InputFilters | null | undefined;
}

export interface TestWiring {
  input_wirings: InputWiring[];
  output_wirings: OutputWiring[];
}

export type InputOrOutputWiring = InputWiring | OutputWiring;

/**
 * ADAPTET INTERFACES
 */
export enum PrimitiveDataType {
  INT = 'int',
  FLOAT = 'float',
  STRING = 'string',
  BOOL = 'boolean',
  ANY = 'any'
}

export enum DataStructureType {
  METADATA = 'metadata',
  TIME_SERIES = 'timeseries',
  SERIES = 'series',
  DATA_FRAME = 'dataframe'
}

// TODO typescript 4.1 ships a new feature called Template Literal Types which allows model set of specific strings.
// We cannot use it now due Angular do not support ts 4.1 at the moment, but in the next 11.1.x version.
export enum AdapterDataType {
  METADATA_ANY = 'metadata(any)',
  METADATA_BOOL = 'metadata(boolean)',
  METADATA_FLOAT = 'metadata(float)',
  METADATA_INT = 'metadata(int)',
  METADATA_STRING = 'metadata(string)',
  SERIES_ANY = 'series(any)',
  SERIES_BOOL = 'series(boolean)',
  SERIES_FLOAT = 'series(float)',
  SERIES_INT = 'series(int)',
  SERIES_STRING = 'series(string)',
  TIME_SERIES_ANY = 'timeseries(any)',
  TIME_SERIES_BOOL = 'timeseries(boolean)',
  TIME_SERIES_FLOAT = 'timeseries(float)',
  TIME_SERIES_INT = 'timeseries(int)',
  TIME_SERIES_STING = 'timeseries(string)',
  DATA_FRAME = 'dataframe',
  ANY = 'any',
  BOOL = 'boolean',
  FLOAT = 'float',
  INT = 'int',
  STRING = 'string',
  MULTITSFRAME = 'multitsframe'
}

export const adapterTypeIoTypeMap = {
  [AdapterDataType.ANY]: IOType.ANY,
  [AdapterDataType.BOOL]: IOType.BOOLEAN,
  [AdapterDataType.FLOAT]: IOType.FLOAT,
  [AdapterDataType.INT]: IOType.INT,
  [AdapterDataType.STRING]: IOType.STRING,
  [AdapterDataType.DATA_FRAME]: IOType.DATAFRAME,
  [AdapterDataType.MULTITSFRAME]: IOType.MULTITSFRAME
};

export interface Adapter {
  id: string;
  name: string;
  url: string;
}

export interface AdapterData {
  id: number;
  name: string;
  thingNodes: ThingNode[];
  sources: SourceSinkNode[];
  sinks: SourceSinkNode[];
}

export interface ThingNode {
  id: string;
  name: string;
  parentId: string | null;
  description: string;
}

export interface SourceSinkNode {
  id: string;
  name: string;
  thingNodeId: string;
  type: AdapterDataType;
  visible: boolean;
  path: string;
  metadataKey?: string;
  filters?:
    | DataSourceSinkDateRangeFilter
    | Record<string, never>
    | null
    | undefined;
}

export interface MetaData {
  key: string;
  value: string;
  dataType: PrimitiveDataType;
}

interface PageAbleDataSource {
  resultCount: number;
  sources: SourceSinkNode[];
}

interface PageAbleDataSink {
  resultCount: number;
  sinks: SourceSinkNode[];
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
  static readonly MANUAL_INPUT_ADAPTER_ID: string = 'direct_provisioning';
  static readonly MANUAL_INPUT_ADAPTER: Omit<Adapter, 'url'> = {
    id: AdapterHttpService.MANUAL_INPUT_ADAPTER_ID,
    name: 'manual input'
  };

  constructor(private readonly http: HttpClient) {}

  static isSourceOrSinkNode(value: any): value is SourceSinkNode {
    return value && 'thingNodeId' in value && 'visible' in value;
  }

  static isDateFilter(value: any): value is DataSourceSinkDateRangeFilter {
    return value && 'fromTimestamp' in value && 'toTimestamp' in value;
  }

  /**
   * Filters nodes by Datatype via ioType
   * -- will ignore nodes without a data type --
   */
  static filterNodesByIoType<T extends { type?: AdapterDataType }>(
    nodes: T[],
    ioType?: IOType
  ): T[] {
    if (Utils.isNullOrUndefined(ioType)) {
      return nodes;
    }

    return nodes.filter(node => {
      // for nodes without dataType, do not filter
      if (Utils.isNullOrUndefined(node.type)) {
        return true;
      }

      return AdapterHttpService.getIOTypeFromAdapterType(node.type) === ioType;
    });
  }

  static isIncompatibleWithIoType(
    type: AdapterDataType | PrimitiveDataType,
    ioType: IOType
  ): boolean {
    return AdapterHttpService.getIOTypeFromAdapterType(type) !== ioType;
  }

  static getIOTypeFromAdapterType(
    adapterDataType: AdapterDataType | PrimitiveDataType
  ): IOType {
    const hasDataStructurePrefix = adapterDataType.split('(').length > 1;
    if (
      (hasDataStructurePrefix &&
        adapterDataType.includes(DataStructureType.SERIES)) ||
      adapterDataType.includes(DataStructureType.TIME_SERIES)
    ) {
      return IOType.SERIES;
    }
    // extract primitive data type from adapter data type
    // for example Adapter data type = timeseries[int]
    const primitiveDataType = hasDataStructurePrefix
      ? (adapterDataType.split('(')[1].split(')')[0] as PrimitiveDataType)
      : (adapterDataType as unknown as PrimitiveDataType);

    return adapterTypeIoTypeMap[primitiveDataType];
  }

  // getAdapterList(): Observable<Adapter[]> {
  //   const url = `${this._apiEndpoint}/adapters/`;
  //   return this.http.get<Adapter[]>(url);
  // }

  /**
   * @param parentThingNodeId if null root nodes will be returned.
   */
  getNodesOfAdapter(
    url: string,
    parentThingNodeId?: string
  ): Observable<AdapterData> {
    const apiUrl = `${url}/structure`;

    let params = null;
    if (Utils.isDefined(parentThingNodeId)) {
      params = { parentId: parentThingNodeId };
    }

    return this.http.get<AdapterData>(apiUrl, {
      params: params ? params : undefined
    });
  }

  getOneSource(
    sourceNodeId: string,
    adapterUrl: string
  ): Observable<SourceSinkNode> {
    const apiUrl = `${adapterUrl}/sources/${sourceNodeId}`;
    return this.http.get<SourceSinkNode>(apiUrl);
  }

  getOneSink(
    sinkNodeId: string,
    adapterUrl: string
  ): Observable<SourceSinkNode> {
    const apiUrl = `${adapterUrl}/sinks/${sinkNodeId}`;
    return this.http.get<SourceSinkNode>(apiUrl);
  }

  getOneThingNode(
    thingNodeId: string,
    adapterUrl: string
  ): Observable<ThingNode> {
    const apiUrl = `${adapterUrl}/thingNodes/${thingNodeId}`;
    return this.http.get<ThingNode>(apiUrl);
  }

  getSources({
    adapterUrl,
    stringFilter
  }: {
    adapterUrl: string;
    sourceId?: string;
    stringFilter?: string;
  }): Observable<SourceSinkNode[]> {
    const apiUrl = `${adapterUrl}/sources`;
    let params: HttpParams = new HttpParams();

    if (Utils.isDefined(stringFilter)) {
      params = params.set('filter', stringFilter);
    }

    return this.http
      .get<PageAbleDataSource>(apiUrl, {
        params
      })
      .pipe(map(pageableDataSource => pageableDataSource.sources));
  }

  getSinks({
    adapterUrl,
    stringFilter
  }: {
    adapterUrl: string;
    sourceId?: string;
    stringFilter?: string;
  }): Observable<SourceSinkNode[]> {
    const apiUrl = `${adapterUrl}/sinks`;
    let params: HttpParams = new HttpParams();
    if (Utils.isDefined(stringFilter)) {
      params = params.set('filter', stringFilter);
    }
    return this.http
      .get<PageAbleDataSink>(apiUrl, {
        params
      })
      .pipe(map(pageableDataSource => pageableDataSource.sinks));
  }

  getAllSourceMetadata(
    adapterUrl: string,
    sourceId: string
  ): Observable<MetaData[]> {
    return this.http.get<MetaData[]>(`${adapterUrl}/sources/${sourceId}`);
  }

  getAllSinkMetadata(
    adapterUrl: string,
    sinkId: string
  ): Observable<MetaData[]> {
    return this.http.get<MetaData[]>(`${adapterUrl}/sinks/${sinkId}`);
  }

  getAllThingNodeMetadata(
    adapterUrl: string,
    thingNodeId: string
  ): Observable<MetaData[]> {
    return this.http.get<MetaData[]>(
      `$${adapterUrl}/thingNodes/${thingNodeId}`
    );
  }

  getMetadataOfSource(
    adapterUrl: string,
    sourceId: string
  ): Observable<MetaData[]> {
    return this.http.get<MetaData[]>(
      `${adapterUrl}/sources/${sourceId}/metadata/`
    );
  }

  getMetadataOfSink(
    adapterUrl: string,
    sinkId: string
  ): Observable<MetaData[]> {
    return this.http.get<MetaData[]>(`${adapterUrl}/sinks/${sinkId}/metadata/`);
  }

  getMetadataOfThingNode(
    adapterUrl: string,
    thinkNodeId: string
  ): Observable<MetaData[]> {
    return this.http.get<MetaData[]>(
      `${adapterUrl}/thingNodes/${thinkNodeId}/metadata/`
    );
  }
}
