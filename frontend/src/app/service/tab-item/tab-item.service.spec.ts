import { TestBed } from '@angular/core/testing';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { Subject } from 'rxjs';
import { TabItemType } from 'src/app/model/tab-item';
import { Transformation } from 'src/app/model/transformation';
import { addTabItem } from 'src/app/store/tab-item/tab-item.actions';
import { LocalStorageService } from '../local-storage/local-storage.service';
import { QueryParameterService } from '../query-parameter/query-parameter.service';
import { TransformationService } from '../transformation/transformation.service';
import { TabItemService } from './tab-item.service';

describe('TabItemService', () => {
  let service: TabItemService;
  let store: MockStore;
  let transformationService: jasmine.SpyObj<TransformationService>;
  let fullTransformation: Subject<Transformation>;

  beforeEach(() => {
    transformationService = jasmine.createSpyObj<TransformationService>(
      'TransformationService',
      ['getFullTransformation']
    );
    fullTransformation = new Subject<Transformation>();
    transformationService.getFullTransformation.and.returnValue(
      fullTransformation
    );

    TestBed.configureTestingModule({
      providers: [
        provideMockStore(),
        {
          provide: TransformationService,
          useValue: transformationService
        },
        {
          provide: LocalStorageService,
          useValue: jasmine.createSpyObj<LocalStorageService>(
            'LocalStorageService',
            ['addToLastOpened']
          )
        },
        {
          provide: QueryParameterService,
          useValue: jasmine.createSpyObj<QueryParameterService>(
            'QueryParameterService',
            ['addQueryParameter']
          )
        }
      ]
    });
    service = TestBed.inject(TabItemService);
    store = TestBed.inject(MockStore);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should open a transformation tab once the full transformation is loaded', () => {
    const dispatchSpy = spyOn(store, 'dispatch');

    service.addTransformationTab('mockId');

    expect(transformationService.getFullTransformation).toHaveBeenCalledWith(
      'mockId'
    );
    expect(dispatchSpy).not.toHaveBeenCalled();

    fullTransformation.next({ id: 'mockId' } as Transformation);

    expect(dispatchSpy).toHaveBeenCalledOnceWith(
      addTabItem({
        transformationId: 'mockId',
        tabItemType: TabItemType.TRANSFORMATION
      })
    );
  });

  it('should open a documentation tab once the full transformation is loaded', () => {
    const dispatchSpy = spyOn(store, 'dispatch');

    service.addDocumentationTab('mockId', true);

    expect(dispatchSpy).not.toHaveBeenCalled();

    fullTransformation.next({ id: 'mockId' } as Transformation);

    expect(dispatchSpy).toHaveBeenCalledOnceWith(
      addTabItem({
        transformationId: 'mockId',
        tabItemType: TabItemType.DOCUMENTATION,
        initialDocumentationEditMode: true
      })
    );
  });
});
