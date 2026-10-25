import React from 'react';
import { ShieldAlert, Accessibility, Utensils } from 'lucide-react';

export function AdvisoryBadge({ dressCode, accessibilityRating, dietaryTag }) {
  return (
    <div className="flex flex-wrap gap-1.5 text-xs">
      {accessibilityRating >= 4 && (
        <span 
          title={`Accessibility Rating: ${accessibilityRating}/5 (Paved, low stairs, senior/family friendly)`}
          className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200"
        >
          <Accessibility className="w-3 h-3 text-blue-500" />
          Accessible ({accessibilityRating}/5)
        </span>
      )}

      {dressCode && dressCode.toLowerCase().includes('modest') && (
        <span 
          title={dressCode}
          className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200"
        >
          <ShieldAlert className="w-3 h-3 text-purple-500" />
          Modest Attire
        </span>
      )}

      {dietaryTag && dietaryTag.includes('pure_veg') && (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-green-50 text-green-700 border border-green-200">
          <Utensils className="w-3 h-3 text-green-500" />
          Pure Veg / Jain
        </span>
      )}
    </div>
  );
}
