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
    let markdown: string;
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
    const displayStyle =
      expression[0] === expression[1] && expression[0] === '$';
    let content = expression.substr(
      displayStyle ? 2 : 1,
      expression.length - (displayStyle ? 4 : 2)
    );
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
