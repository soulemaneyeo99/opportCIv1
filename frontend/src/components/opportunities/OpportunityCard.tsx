import Link from 'next/link'

interface Opportunity {
  id: string
  title: string
  slug: string
  organization: string
  opportunity_type: string
  type_display: string
  location: string
  is_remote: boolean
  deadline: string
  days_until_deadline: number
  is_expired: boolean
  time_left: string
  featured: boolean
}

interface OpportunityCardProps {
  opportunity: Opportunity
  showMatchScore?: boolean
  matchScore?: number
  matchReasons?: string[]
}

export default function OpportunityCard({
  opportunity,
  showMatchScore = false,
  matchScore,
  matchReasons = [],
}: OpportunityCardProps) {
  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      scholarship: 'bg-purple-100 text-purple-800 border-purple-200',
      internship: 'bg-blue-100 text-blue-800 border-blue-200',
      job: 'bg-green-100 text-green-800 border-green-200',
      training: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      competition: 'bg-red-100 text-red-800 border-red-200',
    }
    return colors[type] || 'bg-gray-100 text-gray-800 border-gray-200'
  }

  return (
    <Link
      href={`/opportunities/${opportunity.slug}`}
      className={`block bg-white rounded-xl shadow-sm hover:shadow-lg transition-all p-6 border-2 ${
        opportunity.featured ? 'border-orange-400' : 'border-transparent'
      } hover:border-orange-300`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-xs px-2.5 py-1 rounded-full border ${getTypeColor(opportunity.opportunity_type)}`}>
            {opportunity.type_display}
          </span>
          {opportunity.featured && (
            <span className="text-orange-500" title="Mise en avant">★</span>
          )}
          {opportunity.is_remote && (
            <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">Remote</span>
          )}
        </div>
        {showMatchScore && matchScore !== undefined && (
          <div className="text-right ml-2">
            <div className="text-xl font-bold text-orange-600">{matchScore}%</div>
            <div className="text-xs text-gray-400">match</div>
          </div>
        )}
      </div>

      {/* Title */}
      <h3 className="text-lg font-semibold mb-2 line-clamp-2 text-gray-900">
        {opportunity.title}
      </h3>

      {/* Organization */}
      <p className="text-gray-600 text-sm mb-2">{opportunity.organization}</p>

      {/* Location */}
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-3">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <span>{opportunity.location || 'Non spécifié'}</span>
      </div>

      {/* Match Reasons */}
      {showMatchScore && matchReasons.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {matchReasons.slice(0, 2).map((reason, i) => (
            <span key={i} className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded">
              {reason}
            </span>
          ))}
        </div>
      )}

      {/* Deadline */}
      <div className="flex justify-between items-center pt-3 border-t border-gray-100">
        <span className={`text-sm font-medium ${
          opportunity.is_expired
            ? 'text-red-600'
            : opportunity.days_until_deadline <= 7
              ? 'text-orange-600'
              : 'text-gray-600'
        }`}>
          {opportunity.is_expired ? '❌ Expiré' : `⏰ ${opportunity.time_left}`}
        </span>
        <span className="text-orange-600 text-sm font-medium">
          Voir détails →
        </span>
      </div>
    </Link>
  )
}
