import api from './api'

/**
 * Servicio para consultas al lexicón (Mentor Bora)
 */
export async function searchLexicon({ q, topK = 10, minSimilarity = 0.7, category = null, fast = false }) {
  const params = {
    q,
    top_k: topK,
    min_similarity: minSimilarity,
    fast
  }
  if (category && category.trim()) {
    params.category = category.trim()
  }
  // Refuerza timeout para esta consulta específica (hasta 45s)
  const { data } = await api.get('/lexicon/search', { params, timeout: 45000 })
  return data // { answer: string, results: Array }
}

export async function chatWithLexicon({
  q,
  topK = 10,
  minSimilarity = 0.7,
  category = null,
  fast = false,
  conversationId = null
}) {
  const payload = {
    q,
    top_k: topK,
    min_similarity: minSimilarity,
    fast
  }

  if (category && category.trim()) {
    payload.category = category.trim()
  }

  if (conversationId) {
    payload.conversation_id = conversationId
  }

  const { data } = await api.post('/lexicon/chat', payload, { timeout: 45000 })
  return data // { answer, results, conversation_id }
}

export default { searchLexicon, chatWithLexicon }
