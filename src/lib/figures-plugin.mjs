// Sätteri mdast plugin: standalone images become <figure> "plates", and links to
// audio files get an inline player next to them.
import { defineMdastPlugin } from 'satteri';

const esc = (s = '') => s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
const AUDIO = /\.(wav|mp3|ogg|m4a)$/i;
const text = (node) => (node.value ?? '') + (node.children ?? []).map(text).join('');

export const figuresPlugin = defineMdastPlugin({
  name: 'figures',
  paragraph(node, ctx) {
    const kids = node.children.filter((c) => !(c.type === 'text' && !c.value.trim()));
    if (kids.length !== 1 || kids[0].type !== 'image') return;
    const img = kids[0];
    ctx.replaceNode(node, {
      type: 'html',
      value: `<figure class="plate"><img src="${esc(img.url)}" alt="${esc(img.alt)}" loading="lazy" decoding="async"></figure>`,
    });
  },
  link(node, ctx) {
    if (!AUDIO.test(node.url)) return;
    ctx.replaceNode(node, {
      type: 'html',
      value: `<span class="audio"><audio controls preload="none" src="${esc(node.url)}"></audio><a href="${esc(node.url)}">${esc(text(node))}</a></span>`,
    });
  },
});
