import { CONTRACTS, RISK_CATEGORIES } from './constants'

export const PAGE_SIZE = 25
export const DEFAULT_SORT = 'churn_probability'
export const SORT_COLUMNS = [
  'churn_probability',
  'estimated_revenue_exposure',
  'monthly_charges',
  'tenure',
]
const MAX_PAGE = 100_000 


export function readQuery(searchParams) {
  const get = (key) => searchParams.get(key) ?? ''
  return {
    search: get('search').trim().slice(0, 100),
    contract: CONTRACTS.includes(get('contract')) ? get('contract') : '',
    risk: RISK_CATEGORIES.includes(get('risk')) ? get('risk') : '',
    sort: SORT_COLUMNS.includes(get('sort')) ? get('sort') : DEFAULT_SORT,
    order: get('order') === 'asc' ? 'asc' : 'desc',
    page: Math.min(MAX_PAGE, Math.max(1, Number.parseInt(get('page'), 10) || 1)),
  }
}


export function toSearchParams(query) {
  const params = {}
  if (query.search) params.search = query.search
  if (query.contract) params.contract = query.contract
  if (query.risk) params.risk = query.risk
  if (query.sort !== DEFAULT_SORT) params.sort = query.sort
  if (query.order !== 'desc') params.order = query.order
  if (query.page > 1) params.page = String(query.page)
  return params
}


export function toApiParams(query) {
  const params = { sort_by: query.sort, order: query.order, page: query.page, page_size: PAGE_SIZE }
  if (query.search) params.search = query.search
  if (query.contract) params.contract = query.contract
  if (query.risk) params.risk = query.risk
  return params
}


export function nextSort(query, column) {
  if (query.sort === column) {
    return { ...query, order: query.order === 'desc' ? 'asc' : 'desc', page: 1 }
  }
  return { ...query, sort: column, order: 'desc', page: 1 }
}

export const pageCount = (total, size = PAGE_SIZE) => Math.max(1, Math.ceil(total / size))


export function pageRange(page, count, size = PAGE_SIZE) {
  if (count === 0) return { from: 0, to: 0 }
  const from = (page - 1) * size + 1
  return { from, to: from + count - 1 }
}