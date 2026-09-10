import { Pipe, PipeTransform } from '@angular/core';
import { DomSanitizer } from '@angular/platform-browser';
import { Utils } from '../utils/utils';

@Pipe({
  name: 'highlightText',
  standalone: false
})
export class HighlightTextPipe implements PipeTransform {
  /**
   * The search text is entered by the user and therefore must not be
   * interpreted as a regular expression - "(" alone would throw.
   */
  private static _escapeRegExp(text: string): string {
    return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  constructor(private readonly _sanitizer: DomSanitizer) {}

  transform(value: string | null | undefined, textSearch: string): unknown {
    // adapters are not obliged to provide every attribute, for example the path
    // of a source or sink may be missing
    if (Utils.isNullOrUndefined(value)) {
      return '';
    }

    if (Utils.string.isEmptyOrUndefined(textSearch, false)) {
      return this._sanitizer.bypassSecurityTrustHtml(value);
    }

    const highlightedText = value.replace(
      new RegExp(HighlightTextPipe._escapeRegExp(textSearch), 'gi'),
      match => `<mark>${match}</mark>`
    );
    return this._sanitizer.bypassSecurityTrustHtml(highlightedText);
  }
}
