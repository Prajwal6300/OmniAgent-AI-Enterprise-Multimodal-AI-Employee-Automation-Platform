import React from 'react';

export default function RefundPolicyPage() {
  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-ink mb-6">Refund Policy</h1>
      <div className="prose max-w-none">
        <p>
          <strong>Effective date:</strong> October 15, 2026
        </p>
        <h2 className="text-xl font-semibold text-ink mt-6">Refund Policy</h2>
        <p>
          <strong>DOES-NOT-APPLY: no paid plans yet.</strong> The OmniAgent AI platform is currently provided free of charge. No refund policy is in effect because there are no paid plans, subscriptions, or transactions. Once paid plans are introduced, a formal refund policy will be implemented and this page will be updated accordingly.
        </p>
        <p>
          <strong>Draft - review by a qualified lawyer before launch.</strong>
        </p>
      </div>
    </div>
  );
}