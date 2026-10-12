import { TestBed } from '@angular/core/testing';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { of, Subject } from 'rxjs';
import { RevisionState } from 'src/app/enums/revision-state';
import { TransformationType } from 'src/app/enums/transformation-type';
import { TabItemType } from 'src/app/model/tab-item';
import {
  ComponentTransformation,
  TrafoUpdateState,
  Transformation
} from 'src/app/model/transformation';
import { IAppState } from 'src/app/store/app.state';
import { initialExecutionProtocolState } from 'src/app/store/execution-protocol/execution-protocol.state';
import {
  setAllTransformations,
  updateTransformation
} from 'src/app/store/transformation/transformation.actions';
import { TransformationHttpService } from '../http-service/transformation-http.service';
import { TransformationService } from './transformation.service';

describe('TransformationService', () => {
  let transformationService: TransformationService;
  let transformationHttpService: jasmine.SpyObj<TransformationHttpService>;
  let store: MockStore<IAppState>;

  function createFullTransformation(id: string): ComponentTransformation {
    return {
      id,
      revision_group_id: 'mockGroupId',
      name: 'sum',
      description: 'mock description',
      category: 'EXAMPLES',
      version_tag: '0.0.1',
      state: RevisionState.RELEASED,
      type: TransformationType.COMPONENT,
      documentation: 'mock documentation',
      content: 'python code',
      io_interface: {
        inputs: [],
        outputs: []
      },
      test_wiring: {
        input_wirings: [],
        output_wirings: []
      }
    };
  }

  function createStub(id: string): Transformation {
    const stub: Partial<ComponentTransformation> = createFullTransformation(id);
    delete stub.content;
    delete stub.test_wiring;
    delete stub.documentation;
    return stub as Transformation;
  }

  function setStoreState(
    transformations: Transformation[],
    openTabTransformationIds: string[] = []
  ): void {
    const tabItems = openTabTransformationIds.map(transformationId => ({
      id: `${transformationId}-${TabItemType.TRANSFORMATION}`,
      transformationId,
      tabItemType: TabItemType.TRANSFORMATION
    }));
    store.setState({
      transformations: {
        loaded: true,
        ids: transformations.map(transformation => transformation.id),
        entities: Object.fromEntries(
          transformations.map(transformation => [
            transformation.id,
            transformation
          ])
        )
      },
      tabItems: {
        ids: tabItems.map(tabItem => tabItem.id),
        entities: Object.fromEntries(
          tabItems.map(tabItem => [tabItem.id, tabItem])
        ),
        activeTabItemId: null
      },
      executionProtocol: initialExecutionProtocolState
    });
  }

  beforeEach(() => {
    transformationHttpService = jasmine.createSpyObj<TransformationHttpService>(
      'TransformationHttpService',
      [
        'fetchTransformationStubs',
        'fetchTransformation',
        'fetchTransformationsByIds',
        'updateTransformation'
      ]
    );

    TestBed.configureTestingModule({
      providers: [
        provideMockStore(),
        {
          provide: TransformationHttpService,
          useValue: transformationHttpService
        }
      ]
    });
    transformationService = TestBed.inject(TransformationService);
    store = TestBed.inject(MockStore);
    setStoreState([]);
  });

  it('should be created', () => {
    expect(transformationService).toBeTruthy();
  });

  it('fetchAllTransformations should load stubs only if no tab is open', () => {
    transformationHttpService.fetchTransformationStubs.and.returnValue(
      of([createStub('id0'), createStub('id1')])
    );
    const dispatchSpy = spyOn(store, 'dispatch');

    transformationService.fetchAllTransformations();

    expect(
      transformationHttpService.fetchTransformationsByIds
    ).not.toHaveBeenCalled();
    expect(dispatchSpy).toHaveBeenCalledOnceWith(
      setAllTransformations([createStub('id0'), createStub('id1')])
    );
  });

  it('fetchAllTransformations should fully load the transformations of open tabs', () => {
    setStoreState(
      [createFullTransformation('open'), createStub('other')],
      ['open']
    );
    const reloadedOpenTransformation = {
      ...createFullTransformation('open'),
      name: 'changed by import'
    };
    transformationHttpService.fetchTransformationStubs.and.returnValue(
      of([createStub('open'), createStub('other')])
    );
    transformationHttpService.fetchTransformationsByIds.and.returnValue(
      of([reloadedOpenTransformation])
    );
    const dispatchSpy = spyOn(store, 'dispatch');

    transformationService.fetchAllTransformations();

    expect(
      transformationHttpService.fetchTransformationsByIds
    ).toHaveBeenCalledOnceWith(['open']);
    expect(dispatchSpy).toHaveBeenCalledOnceWith(
      setAllTransformations([reloadedOpenTransformation, createStub('other')])
    );
  });

  it('getFullTransformation should take a full transformation from the store', () => {
    const fullTransformation = createFullTransformation('id0');
    setStoreState([fullTransformation]);
    let result: Transformation | undefined;

    transformationService
      .getFullTransformation('id0')
      .subscribe(transformation => (result = transformation));

    expect(result).toEqual(fullTransformation);
    expect(
      transformationHttpService.fetchTransformation
    ).not.toHaveBeenCalled();
  });

  it('getFullTransformation should fetch a stub once and put it into the store', () => {
    setStoreState([createStub('id0')]);
    const response = new Subject<Transformation>();
    transformationHttpService.fetchTransformation.and.returnValue(response);
    const dispatchSpy = spyOn(store, 'dispatch');
    const results: Transformation[] = [];

    transformationService
      .getFullTransformation('id0')
      .subscribe(transformation => results.push(transformation));
    transformationService
      .getFullTransformation('id0')
      .subscribe(transformation => results.push(transformation));
    const fullTransformation = createFullTransformation('id0');
    response.next(fullTransformation);
    response.complete();

    expect(
      transformationHttpService.fetchTransformation
    ).toHaveBeenCalledOnceWith('id0');
    expect(dispatchSpy).toHaveBeenCalledOnceWith(
      updateTransformation(fullTransformation)
    );
    expect(results).toEqual([fullTransformation, fullTransformation]);
  });

  it('ensureFullTransformation should return a given full transformation itself', () => {
    setStoreState([createStub('id0')]);
    const locallyChangedTransformation = {
      ...createFullTransformation('id0'),
      name: 'not yet saved'
    };
    let result: Transformation | undefined;

    transformationService
      .ensureFullTransformation(locallyChangedTransformation)
      .subscribe(transformation => (result = transformation));

    expect(result).toBe(locallyChangedTransformation);
    expect(
      transformationHttpService.fetchTransformation
    ).not.toHaveBeenCalled();
  });

  it('disableTransformation should send the full transformation if given a stub', () => {
    setStoreState([createStub('id0')]);
    const fullTransformation = createFullTransformation('id0');
    transformationHttpService.fetchTransformation.and.returnValue(
      of(fullTransformation)
    );
    transformationHttpService.updateTransformation.and.callFake(
      transformation =>
        of({ ...transformation, update_state: TrafoUpdateState.SUCCESS })
    );

    transformationService.disableTransformation(createStub('id0')).subscribe();

    const sentTransformation =
      transformationHttpService.updateTransformation.calls.mostRecent().args[0];
    expect(sentTransformation.state).toBe(RevisionState.DISABLED);
    expect(sentTransformation.content).toBe(fullTransformation.content);
    expect(sentTransformation.test_wiring).toEqual(
      fullTransformation.test_wiring
    );
    expect(sentTransformation.documentation).toBe(
      fullTransformation.documentation
    );
  });
});
