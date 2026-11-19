<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ file: string; region: string; highlights: string }>()
const sources = import.meta.glob('../scripts/concept_*.py', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>

function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

const highlighted = computed(() => {
  const source = sources[`../scripts/${props.file}`]
  if (!source)
    throw new Error(`Missing concept snippet: ${props.file}`)
  const start = `# region ${props.region}\n`
  const end = `# endregion ${props.region}`
  const body = source.split(start)[1]?.split(end)[0]?.replace(/\n$/, '')
  if (body === undefined)
    throw new Error(`Missing region ${props.region} in ${props.file}`)
  const highlights = new Map<string, string>(JSON.parse(props.highlights))
  const tokens = [...highlights.keys()].filter(Boolean).sort((a, b) => b.length - a.length)
  if (!tokens.length)
    return escapeHtml(body)
  const pattern = new RegExp(tokens.map(token => token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|'), 'g')
  let cursor = 0
  let result = ''
  for (const match of body.matchAll(pattern)) {
    result += escapeHtml(body.slice(cursor, match.index))
    const cssClass = escapeHtml(highlights.get(match[0]) || '')
    result += `<span class="${cssClass}">${escapeHtml(match[0])}</span>`
    cursor = match.index! + match[0].length
  }
  return result + escapeHtml(body.slice(cursor))
})
</script>

<template>
  <pre class="concept-code"><code v-html="highlighted" /></pre>
</template>
