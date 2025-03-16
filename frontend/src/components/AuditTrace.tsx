import React from 'react';

interface Props {
  auditRecords: any[];
}

export default function AuditTrace({ auditRecords }: Props) {
  return (
    <div className="p-4 bg-gray-800 rounded-lg">
      <h2 className="text-lg font-semibold mb-2">Audit Trace</h2>
      {auditRecords && auditRecords.length > 0 ? (
        <ul className="text-sm space-y-1 max-h-48 overflow-y-auto">
          {auditRecords.map((rec) => (
            <li key={rec.audit_id} className="border-b border-gray-700 pb-1">
              <span className="font-mono text-xs text-gray-500">{rec.timestamp}</span>
              <div>
                Recommendation: {rec.recommendation || 'N/A'}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-gray-400">No audit records.</p>
      )}
    </div>
  );
}
