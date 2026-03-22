import DOMPurify from 'isomorphic-dompurify';
import { marked } from 'marked';

marked.setOptions({ gfm: true, breaks: true });

/** Markdown → HTML seguro para {@html ...}. */
export function renderMarkdown(md: string): string {
	if (!md?.trim()) return '';
	const raw = marked.parse(md, { async: false }) as string;
	return DOMPurify.sanitize(raw);
}
