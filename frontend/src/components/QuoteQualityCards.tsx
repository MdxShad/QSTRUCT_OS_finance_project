import React from 'react';

interface Props {
  riskAssessment: any | null;
  winProbability: number | null;
  deskEconomics: number | null;
}

export default function QuoteQualityCards({ riskAssessment, winProbability, deskEconomics }: Props) {
  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="p-4 bg-gray-800 rounded-lg">
        <h3 className="text-sm font-semibold">Win Probability</h3>
        <p className="text-xl font-bold">{winProbability !== null ? (winProbability * 100).toFixed(1) + '%' : '--'}</p>
      </div>
      <div className="p-4 bg-gray-800 rounded-lg">
        <h3 className="text-sm font-semibold">Desk Economics</h3>
        <p className="text-xl font-bold">{deskEconomics !== null ? (deskEconomics * 100).toFixed(1) + '%' : '--'}</p>
      </div>
      <div className="p-4 bg-gray-800 rounded-lg">
        <h3 className="text-sm font-semibold">Risk Score</h3>
        <p className="text-xl font-bold">{riskAssessment ? (riskAssessment.overall_risk_score * 100).toFixed(1) + '%' : '--'}</p>
      </div>
    </div>
  );
}
