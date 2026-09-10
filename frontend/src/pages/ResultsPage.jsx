/**
 * Results Page — Part of Person 1 (Frontend Lead)'s workspace
 *
 * Displays the full inspection result for a single product:
 *   - Tier badge (compliant / review / violation)
 *   - Declaration fields with status indicators
 *   - Font-size check results
 *   - Evidence record (hash, timestamp)
 *
 * Currently renders mock data. Wire to GET /results/{id} once backend is live.
 *
 * TODO(Person 1): Fetch real data from API using the :id route param.
 */

import { useParams } from 'react-router-dom'
import mockData from '../data/mock_data.json'

const TIER_LABELS = {
  likely_compliant: { label: 'Likely Compliant', emoji: '✅' },
  needs_review: { label: 'Needs Review', emoji: '⚠️' },
  likely_violation: { label: 'Likely Violation', emoji: '🚫' },
}

const STATUS_COLORS = {
  pass: 'text-compliant',
  fail: 'text-violation',
  flag: 'text-review',
}

const STATUS_ICONS = {
  pass: '✓',
  fail: '✗',
  flag: '⚑',
}

export default function ResultsPage() {
  const { id } = useParams()

  // TODO(Person 1): Replace with real API fetch:
  //   const [result, setResult] = useState(null)
  //   useEffect(() => {
  //     fetch(`/api/results/${id}`).then(r => r.json()).then(setResult)
  //   }, [id])

  // For now, find matching mock or use the first one
  const result = id
    ? mockData.find((r) => r.id === id) || mockData[0]
    : mockData[0]

  const tier = TIER_LABELS[result.compliance_result.tier] || TIER_LABELS.needs_review

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-1">{result.product_name}</h1>
          <p className="text-slate-500 text-sm">
            Inspection ID: <code className="text-slate-400">{result.id}</code>
            {' • '}
            {new Date(result.created_at).toLocaleString()}
          </p>
        </div>
        <div className={`tier-${result.compliance_result.tier} px-5 py-2.5 rounded-xl text-sm font-bold`}>
          {tier.emoji} {tier.label}
        </div>
      </div>

      {/* Declaration Fields */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-4 text-slate-200">📋 Declarations</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(result.declarations).map(([key, field]) => (
            <div key={key} className="glass rounded-xl p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs uppercase tracking-wider text-slate-500 font-semibold">
                  {key.replace('_', ' ')}
                </span>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  field.status === 'present'
                    ? 'bg-compliant/15 text-compliant'
                    : field.status === 'missing'
                      ? 'bg-violation/15 text-violation'
                      : 'bg-review/15 text-review'
                }`}>
                  {field.status}
                </span>
              </div>
              <p className="text-lg font-medium text-white">
                {field.value || '—'}
              </p>
              <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                <span>Confidence: {(field.confidence * 100).toFixed(0)}%</span>
                {field.bbox && (
                  <span>BBox: {field.bbox.w}×{field.bbox.h}px</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Compliance Verdicts */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-4 text-slate-200">⚖️ Compliance Check</h2>
        <div className="glass rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5">
                <th className="text-left px-5 py-3 text-slate-500 font-medium">Field</th>
                <th className="text-left px-5 py-3 text-slate-500 font-medium">Status</th>
                <th className="text-left px-5 py-3 text-slate-500 font-medium">Reason</th>
              </tr>
            </thead>
            <tbody>
              {result.compliance_result.compliance.map((c, i) => (
                <tr key={i} className="border-b border-white/5 last:border-0">
                  <td className="px-5 py-3 font-medium text-slate-200 capitalize">{c.field.replace('_', ' ')}</td>
                  <td className={`px-5 py-3 font-bold ${STATUS_COLORS[c.status]}`}>
                    {STATUS_ICONS[c.status]} {c.status.toUpperCase()}
                  </td>
                  <td className="px-5 py-3 text-slate-400">{c.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Font-Size Check */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-4 text-slate-200">🔤 Font Size Check</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {result.compliance_result.font_check.map((fc, i) => (
            <div key={i} className="glass rounded-xl p-5">
              <div className="flex items-center justify-between mb-3">
                <span className="font-medium text-slate-200 capitalize">{fc.field.replace('_', ' ')}</span>
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                  fc.status === 'pass'
                    ? 'bg-compliant/15 text-compliant'
                    : 'bg-violation/15 text-violation'
                }`}>
                  {fc.status.toUpperCase()}
                </span>
              </div>
              {/* Ratio bar visualization */}
              <div className="relative h-2 bg-surface-lighter rounded-full mb-2 overflow-hidden">
                <div
                  className={`absolute top-0 left-0 h-full rounded-full transition-all ${
                    fc.status === 'pass' ? 'bg-compliant' : 'bg-violation'
                  }`}
                  style={{ width: `${Math.min(fc.ratio / 0.06, 1) * 100}%` }}
                />
                {/* Threshold marker */}
                <div
                  className="absolute top-0 h-full w-0.5 bg-white/40"
                  style={{ left: `${(fc.threshold / 0.06) * 100}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-slate-500">
                <span>Ratio: {(fc.ratio * 100).toFixed(1)}%</span>
                <span>Threshold: {(fc.threshold * 100).toFixed(1)}%</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Evidence Record */}
      <section>
        <h2 className="text-lg font-semibold mb-4 text-slate-200">🔒 Evidence Record</h2>
        <div className="glass rounded-xl p-5">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
            <div>
              <span className="text-slate-500 text-xs uppercase tracking-wider">Image</span>
              <p className="text-slate-200 font-mono text-xs mt-1 break-all">{result.evidence.image_url}</p>
            </div>
            <div>
              <span className="text-slate-500 text-xs uppercase tracking-wider">SHA-256 Hash</span>
              <p className="text-slate-200 font-mono text-xs mt-1 break-all">{result.evidence.sha256_hash}</p>
            </div>
            <div>
              <span className="text-slate-500 text-xs uppercase tracking-wider">Timestamp</span>
              <p className="text-slate-200 text-xs mt-1">{new Date(result.evidence.timestamp).toLocaleString()}</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
