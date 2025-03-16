import React from 'react';

interface Props {
  alternatives: any[];
  recommendedId: string | null;
}

export default function AlternativesTable({ alternatives, recommendedId }: Props) {
  return (
    <div className="p-4 bg-gray-800 rounded-lg">
      <h2 className="text-lg font-semibold mb-2">Counterfactual Alternatives</h2>
      {alternatives && alternatives.length > 0 ? (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700 text-left">
              <th className="py-1">ID</th>
              <th className="py-1">Title</th>
              <th className="py-1">Final Score</th>
              <th className="py-1">Win Prob</th>
              <th className="py-1">Desk Econ</th>
              <th className="py-1">Risk</th>
            </tr>
          </thead>
          <tbody>
            {alternatives.map((alt) => (
              <tr
                key={alt.alternative_id}
                className={
                  'border-b border-gray-700' +
                  (alt.alternative_id === recommendedId ? ' bg-blue-800/20' : '')
                }
              >
                <td className="py-1">{alt.alternative_id.slice(0, 6)}</td>
                <td className="py-1">{alt.title}</td>
                <td className="py-1">{(alt.final_score * 100).toFixed(1)}%</td>
                <td className="py-1">{(alt.win_probability * 100).toFixed(1)}%</td>
                <td className="py-1">{(alt.desk_economics_score * 100).toFixed(1)}%</td>
                <td className="py-1">{(alt.risk_score * 100).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="text-sm text-gray-400">No alternatives generated.</p>
      )}
    </div>
  );
}
