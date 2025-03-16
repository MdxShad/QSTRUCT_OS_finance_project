import React from 'react';

interface Props {
  explanation: string | null;
}

export default function ExplanationPanel({ explanation }: Props) {
  return (
    <div className="p-4 bg-gray-800 rounded-lg">
      <h2 className="text-lg font-semibold mb-2">Explanation</h2>
      <p className="text-sm text-gray-300 whitespace-pre-line">
        {explanation || 'No explanation available.'}
      </p>
    </div>
  );
}
