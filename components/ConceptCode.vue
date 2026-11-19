<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  file: string
  region: string
  highlights: string
  highlightLine?: string
}>()
const sources = import.meta.glob('../scripts/*.py', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>

function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

const sourceCode = computed(() => {
  const source = sources[`../scripts/${props.file}`]
  if (!source)
    throw new Error(`Missing concept snippet: ${props.file}`)
  const start = `# region ${props.region}\n`
  const end = `# endregion ${props.region}`
  let body = source.split(start)[1]?.split(end)[0]?.trimEnd()
  if (body === undefined)
    throw new Error(`Missing region ${props.region} in ${props.file}`)
  return body
})

const highlighted = computed(() => {
  const body = sourceCode.value
  const highlights = new Map<string, string>(JSON.parse(props.highlights))
  const tokens = [...highlights.keys()].filter(Boolean).sort((a, b) => b.length - a.length)
  if (!tokens.length)
    return escapeHtml(body)
  const pattern = new RegExp(tokens.map(token => {
    const escaped = token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    return /^\w+$/.test(token) ? `\\b${escaped}\\b` : escaped
  }).join('|'), 'g')
  const rangeStart = props.highlightLine ? body.indexOf(props.highlightLine) : 0
  if (rangeStart < 0)
    throw new Error(`Missing highlight line in ${props.file}`)
  const rangeEnd = props.highlightLine ? rangeStart + props.highlightLine.length : body.length
  let cursor = 0
  let result = ''
  for (const match of body.matchAll(pattern)) {
    if (match.index! < rangeStart || match.index! + match[0].length > rangeEnd)
      continue
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
