import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterModule } from '@angular/router';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { NEVER, Observable, of, throwError } from 'rxjs';
import { BasicTestModule } from 'src/app/basic-test.module';
import { RevisionState } from 'src/app/enums/revision-state';
import { ContainingWorkflow } from 'src/app/model/containing-workflow';
import { Transformation } from 'src/app/model/transformation';
import { TransformationHttpService } from 'src/app/service/http-service/transformation-http.service';
import { selectHashedTransformationLookupById } from 'src/app/store/transformation/transformation.selectors';
import { ContainingWorkflowsComponent } from './containing-workflows.component';

describe('ContainingWorkflowsComponent', () => {
  let fixture: ComponentFixture<ContainingWorkflowsComponent>;
  let transformationHttpService: jasmine.SpyObj<TransformationHttpService>;

  const render = (
    containingWorkflows: Observable<ContainingWorkflow[]>,
    transformationsById: Record<string, Transformation> = {}
  ) => {
    transformationHttpService = jasmine.createSpyObj<TransformationHttpService>(
      'TransformationHttpService',
      { fetchContainingWorkflows: containingWorkflows }
    );
    TestBed.configureTestingModule({
      imports: [BasicTestModule, RouterModule.forRoot([])],
      declarations: [ContainingWorkflowsComponent],
      providers: [
        provideMockStore(),
        {
          provide: TransformationHttpService,
          useValue: transformationHttpService
        }
      ]
    });
    TestBed.inject(MockStore).overrideSelector(
      selectHashedTransformationLookupById,
      transformationsById
    );
    fixture = TestBed.createComponent(ContainingWorkflowsComponent);
    fixture.componentInstance.transformationId = 'transformation-id';
    fixture.detectChanges();
  };

  const normalizedText = (element: Element): string =>
    element.textContent.replace(/\s+/g, ' ').trim();

  const renderedText = (): string =>
    normalizedText(fixture.nativeElement as HTMLElement);

  const renderedItems = (): string[] =>
    Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll('li'),
      normalizedText
    );

  it('lists the workflows containing the transformation directly or nested', () => {
    render(
      of([
        {
          id: 'inner-id',
          name: 'Inner',
          version_tag: '1.0.0',
          state: RevisionState.RELEASED,
          direct_operator_ids: ['operator-1', 'operator-2'],
          via_workflow_ids: []
        },
        {
          id: 'outer-id',
          name: 'Outer',
          version_tag: '2.0.0',
          state: RevisionState.DRAFT,
          direct_operator_ids: ['operator-3'],
          via_workflow_ids: ['inner-id']
        },
        {
          id: 'top-id',
          name: 'Top',
          version_tag: '0.1.0',
          state: RevisionState.DISABLED,
          direct_operator_ids: [],
          via_workflow_ids: ['outer-id', 'changed-draft-id']
        }
      ]),
      // a nested DRAFT workflow which no longer contains the transformation
      // since Top was stored is not in the response, but in the store
      {
        'changed-draft-id': {
          name: 'Changed Draft',
          version_tag: '0.0.1'
        } as Transformation
      }
    );

    expect(
      transformationHttpService.fetchContainingWorkflows
    ).toHaveBeenCalledWith('transformation-id');
    expect(renderedText()).toContain('Used in 3 workflows:');
    expect(renderedItems()).toEqual([
      'Inner (1.0.0), released — directly as 2 operators',
      'Outer (2.0.0), draft — directly as 1 operator and indirectly via Inner (1.0.0)',
      'Top (0.1.0), deprecated — indirectly via Outer (2.0.0), Changed Draft (0.0.1)'
    ]);
  });

  it('links each workflow, to be opened in a new browser tab', () => {
    render(
      of([
        {
          id: 'workflow-id',
          name: 'Workflow',
          version_tag: '1.0.0',
          state: RevisionState.RELEASED,
          direct_operator_ids: ['operator-id'],
          via_workflow_ids: []
        }
      ])
    );

    expect(renderedText()).toContain('Used in 1 workflow:');
    const link = (fixture.nativeElement as HTMLElement).querySelector('li a');
    expect(link.getAttribute('href')).toBe('/?id=workflow-id');
    expect(link.getAttribute('target')).toBe('_blank');
  });

  it('says so if the transformation is not used in any workflow', () => {
    render(of([]));

    expect(renderedText()).toBe('Not used in any workflow.');
  });

  it('says so while loading', () => {
    render(NEVER);

    expect(renderedText()).toBe('Loading the workflows using this...');
  });

  it('says so if loading fails', () => {
    render(throwError(() => new Error('backend not reachable')));

    expect(renderedText()).toBe('Could not load the workflows using this.');
  });
});
