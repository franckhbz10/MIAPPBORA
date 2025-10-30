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

export default { searchLexicon }
