import { DomSanitizer } from '@angular/platform-browser';
import { HighlightTextPipe } from './highlight-text.pipe';

describe('HighlightTextPipe', () => {
  const sanitizerMock = {
    bypassSecurityTrustHtml: (value: string) => value
  } as unknown as DomSanitizer;

  it('create an instance', () => {
    const pipe = new HighlightTextPipe(sanitizerMock);
    expect(pipe).toBeTruthy();
  });

  it('highlights every occurrence of the search text', () => {
    const pipe = new HighlightTextPipe(sanitizerMock);
    expect(pipe.transform('Plant A / Plant B', 'plant')).toBe(
      '<mark>Plant</mark> A / <mark>Plant</mark> B'
    );
  });

  it('returns an empty string for a missing value', () => {
    // sources and sinks of generic rest adapters may have no path
    const pipe = new HighlightTextPipe(sanitizerMock);
    expect(pipe.transform(undefined, 'plant')).toBe('');
    expect(pipe.transform(null, 'plant')).toBe('');
  });

  it('does not interpret the search text as regular expression', () => {
    const pipe = new HighlightTextPipe(sanitizerMock);
    expect(pipe.transform('Plant A (old)', '(old)')).toBe(
      'Plant A <mark>(old)</mark>'
    );
  });
});
