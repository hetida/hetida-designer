import { HighlightTextPipe } from './highlight-text.pipe';

describe('HighlightTextPipe', () => {
  it('create an instance', () => {
    const pipe = new HighlightTextPipe(null as any);
    expect(pipe).toBeTruthy();
  });
});
