import { TestBed } from '@angular/core/testing';
import { QueryParameterService } from './query-parameter.service';
import { RouterTestingModule } from '@angular/router/testing';
import { AppComponent } from 'src/app/app.component';

describe('QueryParameterService', () => {
  let queryParameterService: QueryParameterService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [
        RouterTestingModule.withRoutes([
          { path: '**', component: AppComponent }
        ])
      ]
    });

    queryParameterService = TestBed.inject(QueryParameterService);
  });

  it('QueryParameterService should be created', () => {
    // Assert
    expect(queryParameterService).toBeTruthy();
  });

  it('Add query parameter should add the passed transformationId', async () => {
    // Arrange
    const mockId = '0-123-abc';
    // Act
    queryParameterService.addQueryParameter(mockId);
    const ids = await queryParameterService.getIdsFromQueryParameters();
    // Assert
    expect(ids).toEqual(['0-123-abc']);
  });

  it('Delete query parameter should delete the passed transformationId', async () => {
    // Arrange
    const mockId0 = '0-123-abc';
    const mockId1 = '1-123-abc';
    // Act
    queryParameterService.addQueryParameter(mockId0);
    queryParameterService.addQueryParameter(mockId1);
    queryParameterService.deleteQueryParameter(mockId0);
    const ids = await queryParameterService.getIdsFromQueryParameters();
    // Assert
    expect(ids).toEqual(['1-123-abc']);
  });
});
