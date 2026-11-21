import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

const config = JSON.parse(readFileSync(new URL('../vercel.json', import.meta.url), 'utf8'))

describe('vercel.json', () => {
  it('sends every address to index.html so deep links and refreshes work', () => {
    expect(config.rewrites).toEqual([{ source: '/(.*)', destination: '/index.html' }])
  })
})