/**
 * MAI Framework V2 - API Service
 *
 * Uses relative paths that work with Caddy reverse proxy.
 * No complex URL resolution needed - /api routes to backend automatically.
 */

// ============================================
// Types
// ============================================

export interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export interface ChatRequest {
  messages: Message[]
  max_tokens?: number
  temperature?: number
  stream?: boolean
}

export interface ChatResponse {
  id: string
  object: string
  created: number
  model: string
  choices: Array<{
    index: number
    message: Message
    finish_reason: string
  }>
  usage?: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
}

export interface StreamChunk {
  content: string
  done: boolean
}

export interface LLMStatusResponse {
  provider: string
  connected: boolean
  model?: string | null
  error?: string | null
}

export interface HealthResponse {
  status: string
  version: string
  services?: {
    mlx: { status: string; connected: boolean; current_model?: string }
    database: { status: string }
    redis: { status: string }
    qdrant: { status: string }
  }
}

// ============================================
// API Configuration
// ============================================

/**
 * API Base URL - Always use relative path.
 * Caddy handles routing /api/* to the backend service.
 * This works for:
 * - localhost (development)
 * - Tailscale IP (100.x.x.x)
 * - MagicDNS hostname (mai-studio.tailnet.ts.net)
 */
const API_BASE = '/api/v1'

/**
 * Generic fetch wrapper with error handling
 */
async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${endpoint}`

  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  }

  const response = await fetch(url, config)

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }))
    throw new Error(error.detail?.message || error.message || `HTTP ${response.status}`)
  }

  return response.json()
}

// ============================================
// Health & Status
// ============================================

export async function getHealth(): Promise<HealthResponse> {
  // Note: /health is at root, not under /api/v1
  const response = await fetch('/health')
  if (!response.ok) throw new Error('Health check failed')
  return response.json()
}

export async function getDetailedHealth(): Promise<HealthResponse> {
  const response = await fetch('/health/detailed')
  if (!response.ok) throw new Error('Health check failed')
  return response.json()
}

export async function getLLMStatus(): Promise<LLMStatusResponse> {
  return apiFetch<LLMStatusResponse>('/agents/llm-status')
}

// ============================================
// Chat Completions
// ============================================

export async function chatCompletion(request: ChatRequest): Promise<ChatResponse> {
  return apiFetch<ChatResponse>('/chat/completions', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

/**
 * Stream chat completions using Server-Sent Events
 */
export async function* streamChatCompletion(
  request: ChatRequest
): AsyncGenerator<StreamChunk> {
  const url = `${API_BASE}/chat/completions`

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ...request, stream: true }),
  })

  if (!response.ok) {
    throw new Error(`Stream failed: ${response.status}`)
  }

  const reader = response.body?.getReader()
  if (!reader) throw new Error('No response body')

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6)
        if (data === '[DONE]') {
          return
        }
        try {
          const chunk = JSON.parse(data)
          yield {
            content: chunk.choices?.[0]?.delta?.content || '',
            done: chunk.choices?.[0]?.finish_reason === 'stop'
          }
        } catch {
          // Skip invalid JSON
        }
      }
    }
  }
}

// ============================================
// API Status
// ============================================

export async function getAPIStatus(): Promise<{ status: string; version: string }> {
  return apiFetch<{ status: string; version: string }>('/status')
}
