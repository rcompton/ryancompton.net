// Render $$...$$ math to static KaTeX HTML at build time (Sätteri mdast plugin).
import katex from 'katex';
import { defineMdastPlugin } from 'satteri';

const render = (value, displayMode) =>
  katex.renderToString(value, { displayMode, throwOnError: false });

export const katexPlugin = defineMdastPlugin({
  name: 'katex',
  inlineMath(node, ctx) {
    ctx.replaceNode(node, { type: 'html', value: render(node.value, false) });
  },
  math(node, ctx) {
    ctx.replaceNode(node, { type: 'html', value: render(node.value, true) });
  },
});
