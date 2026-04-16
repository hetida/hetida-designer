import { SafeHtml, DomSanitizer } from '@angular/platform-browser';
import { Injectable } from '@angular/core';
import { marked } from 'marked';
import katex from 'katex';

@Injectable({
  providedIn: 'root'
})
export class MarkdownService {
  private readonly regex = /\$\$[^\$]*\$\$|\$[^\$]*\$/gm;

  constructor(private readonly domSanitizer: DomSanitizer) {}

  public parseMarkdown(text: string): SafeHtml {
    let markdown = '';
    try {
      markdown = marked.parse(text, { async: false });
      // parsing katex math expression
      const mathBlocks: string[] = markdown.match(this.regex) || [];
      for (const block of mathBlocks) {
        markdown = markdown.replace(block, this.renderMathExpression(block));
      }
    } catch (error) {
      // incomplete markdown can and most likely will lead to a error during parsing
      // we catch them here so the error interceptor doesn't throw notifications
      console.error(error);
    }
    // we need to mark the output as safe, since the sanitizer strips the svg out
    return this.domSanitizer.bypassSecurityTrustHtml(markdown);
  }

  private renderMathExpression(expression: string): string {
    // There are two used styles of math expressions, one is inline and starts, ends with '$'.
    // The other one is a block style and starts, ends with '$$' to flag them.
    // 'displayStyle' verifies for inline or block expression and
    // removes starting and trailing '$' signs from the content, so it can be rendered later.
    const displayStyle =
      expression[0] === expression[1] && expression[0] === '$';
    let content = expression.substr(
      displayStyle ? 2 : 1,
      expression.length - (displayStyle ? 4 : 2)
    );
    // The first replace matches HTML opening and closing tags and removes them,
    // marked will add them if he detects an '<', '>' or '/>' in the math expression.
    content = content
      .replace(/<\/?[^>]+>/g, '')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>');
    let html: string = katex.renderToString(content);
    if (displayStyle) {
      html = html.replace(
        /class="katex"/g,
        'class="katex katex-block" style="display:block;"'
      );
    }
    return html;
  }
}
