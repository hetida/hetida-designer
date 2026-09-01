import { Pipe, PipeTransform } from '@angular/core';
import { DomSanitizer } from '@angular/platform-browser';

@Pipe({
  name: 'highlightText',
  standalone: false
})
export class HighlightTextPipe implements PipeTransform {
  constructor(private readonly _sanitizer: DomSanitizer) {}
  transform(value: string, textSearch: string): unknown {
    const highlightedText = value.replace(
      new RegExp(textSearch, 'gi'),
      match => `<mark>${match}</mark>`
    );
    return this._sanitizer.bypassSecurityTrustHtml(highlightedText);
  }
}
