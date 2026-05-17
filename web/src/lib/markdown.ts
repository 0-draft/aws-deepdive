import DOMPurify from "isomorphic-dompurify";
import { marked } from "marked";

marked.setOptions({ gfm: true, breaks: false });

/**
 * Render Markdown to HTML and sanitize. Report content can include titles
 * and summaries that originated from external RSS / GitHub feeds, so the
 * output must be sanitized before it is fed to `set:html`.
 */
export function md(src: string): string {
  const raw = marked.parse(src, { async: false }) as string;
  return DOMPurify.sanitize(raw, { USE_PROFILES: { html: true } });
}
