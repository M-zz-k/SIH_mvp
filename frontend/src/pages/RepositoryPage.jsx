/**
 * Repository / Search Page — Part of Person 1 (Frontend Lead)'s workspace
 *
 * Displays all past inspection results in a searchable, filterable table.
 * Supports filtering by tier and free-text search by product name.
 *
 * Currently renders all entries from mock_data.json.
 *
 * TODO(Person 1): Wire to GET /results/search/query with query params.
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import mockData from '../data/mock_data.json'

const TIERS = [
  { value: '', label: 'All Tiers' },
  { value: 'likely_compliant', label: '✅ Compliant' },
  { value: 'needs_review', label: '⚠️ Needs Review' },
  { value: 'likely_violation', label: '🚫 Violation' },
]

export default function RepositoryPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [tierFilter, setTierFilter] = useState('')

  // TODO(Person 1): Replace with API call:
  //   const [results, setResults] = useState([])
  //   useEffect(() => {
  //     fetch(`/api/results/search/query?q=${search}&tier=${tierFilter}`)
  //       .then(r => r.json())
  //       .then(d => setResults(d.results))
  //   }, [search, tierFilter])

  const filtered = mockData.filter((r) => {
    const matchesSearch = !search || r.product_name.toLowerCase().includes(search.toLowerCase())
    const matchesTier = !tierFilter || r.compliance_result.tier === tierFilter
    return matchesSearch && matchesTier
  })

  // Stats from filtered data
  const stats = {
    total: filtered.length,
    compliant: filtered.filter(r => r.compliance_result.tier === 'likely_compliant').length,
    review: filtered.filter(r => r.compliance_result.tier === 'needs_review').length,
    violation: filtered.filter(r => r.compliance_result.tier === 'likely_violation').length,
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <h1 className="text-3xl font-bold mb-2">Inspection Repository</h1>
      <p className="text-slate-400 mb-8">Search and review all past inspections</p>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { label: 'Total', value: stats.total, color: 'text-slate-200', bg: 'bg-white/5' },
          { label: 'Compliant', value: stats.compliant, color: 'text-compliant', bg: 'bg-compliant/10' },
          { label: 'Needs Review', value: stats.review, color: 'text-review', bg: 'bg-review/10' },
          { label: 'Violations', value: stats.violation, color: 'text-violation', bg: 'bg-violation/10' },
        ].map(({ label, value, color, bg }) => (
          <div key={label} className={`rounded-xl p-4 ${bg} border border-white/5`}>
            <div className={`text-2xl font-bold ${color}`}>{value}</div>
            <div className="text-xs text-slate-500 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Search & filter bar */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">🔍</span>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by product name…"
            className="w-full pl-10 pr-4 py-3 rounded-xl bg-surface-light border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
          />
        </div>
        <div className="flex gap-2">
          {TIERS.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setTierFilter(value)}
              className={`px-4 py-3 rounded-xl text-sm font-medium transition-all cursor-pointer whitespace-nowrap ${
                tierFilter === value
                  ? 'bg-primary/20 text-primary-light border border-primary/30'
                  : 'bg-surface-light text-slate-400 border border-white/5 hover:border-white/15'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Results table */}
      <div className="glass rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/5">
              <th className="text-left px-5 py-3.5 text-slate-500 font-medium">Product</th>
              <th className="text-left px-5 py-3.5 text-slate-500 font-medium">Date</th>
              <th className="text-left px-5 py-3.5 text-slate-500 font-medium">Tier</th>
              <th className="text-left px-5 py-3.5 text-slate-500 font-medium">Fields</th>
              <th className="text-right px-5 py-3.5 text-slate-500 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r) => {
              const passCount = r.compliance_result.compliance.filter(c => c.status === 'pass').length
              const totalFields = r.compliance_result.compliance.length
              return (
                <tr
                  key={r.id}
                  className="border-b border-white/5 last:border-0 hover:bg-white/[0.02] transition-colors cursor-pointer"
                  onClick={() => navigate(`/results/${r.id}`)}
                >
                  <td className="px-5 py-4">
                    <div className="font-medium text-slate-200">{r.product_name}</div>
                    <div className="text-xs text-slate-500 font-mono">{r.id}</div>
                  </td>
                  <td className="px-5 py-4 text-slate-400">
                    {new Date(r.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-5 py-4">
                    <span className={`tier-${r.compliance_result.tier} px-3 py-1 rounded-lg text-xs font-bold`}>
                      {r.compliance_result.tier.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-slate-400">
                    <span className="text-compliant">{passCount}</span>/{totalFields} pass
                  </td>
                  <td className="px-5 py-4 text-right">
                    <span className="text-primary-light hover:text-primary transition-colors text-xs font-medium">
                      View →
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>

        {filtered.length === 0 && (
          <div className="text-center py-12 text-slate-500">
            No inspections match your search.
          </div>
        )}
      </div>
    </div>
  )
}
