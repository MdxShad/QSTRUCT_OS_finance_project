import React from 'react';

interface Props {
  rawText: string;
  setRawText: (value: string) => void;
  onParse: () => void;
  onOptimize: () => void;
}

const DEMO_RFQ =
  'Client wants 2Y USD autocallable, quarterly observation, worst-of basket on Nvidia, Samsung and HSI, KI 60%, KO 100%, target coupon 11-13%, callable after 6M, note format, APAC distributor.';

export default function RFQInput({ rawText, setRawText, onParse, onOptimize }: Props) {
  return (
    <div className="p-4 bg-gray-800 rounded-lg space-y-2">
      <h2 className="text-lg font-semibold">RFQ Input</h2>
      <textarea
        className="w-full h-32 p-2 bg-gray-900 border border-gray-700 rounded-md text-sm"
        value={rawText}
        onChange={(e) => setRawText(e.target.value)}
        placeholder="Enter free‑form RFQ description"
      />
      <div className="flex space-x-2">
        <button
          className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded-md text-sm"
          onClick={onParse}
        >
          Parse
        </button>
        <button
          className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded-md text-sm"
          onClick={onOptimize}
        >
          Optimize
        </button>
        <button
          className="px-3 py-1 bg-gray-600 hover:bg-gray-700 rounded-md text-sm"
          onClick={() => setRawText(DEMO_RFQ)}
        >
          Seed Demo
        </button>
      </div>
    </div>
  );
}
