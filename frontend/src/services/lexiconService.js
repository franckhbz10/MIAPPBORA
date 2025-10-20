import api from './api'

/**
 * Servicio para consultas al lexicón (Mentor Bora)
 */
export async function searchLexicon({ q, topK = 10, minSimilarity = 0.7, category = null }) {
  const params = {
    q,
    top_k: topK,
    min_similarity: minSimilarity
  }
  if (category && category.trim()) {
    params.category = category.trim()
  }
  const { data } = await api.get('/lexicon/search', { params })
  return data // { answer: string, results: Array }
}

export default { searchLexicon }
