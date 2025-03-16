import React from 'react';

interface Props {
  payoffObject: any | null;
}

export default function PayoffObjectPanel({ payoffObject }: Props) {
  if (!payoffObject) {
    return (
      <div className="p-4 bg-gray-800 rounded-lg">
        <h2 className="text-lg font-semibold">Payoff Object</h2>
        <p className="text-sm text-gray-400">No data</p>
      </div>
    );
  }
  // Filter out null or undefined fields for display
  const entries = Object.entries(payoffObject).filter(([, v]) => v !== null && v !== undefined);
  return (
    <div className="p-4 bg-gray-800 rounded-lg">
      <h2 className="text-lg font-semibold mb-2">Payoff Object</h2>
      <table className="text-sm w-full">
        <tbody>
          {entries.map(([key, value]) => (
            <tr key={key} className="border-b border-gray-700">
              <td className="pr-2 font-medium capitalize">{key.replace(/_/g, ' ')}</td>
              <td className="text-gray-300">{Array.isArray(value) ? value.join(', ') : String(value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
