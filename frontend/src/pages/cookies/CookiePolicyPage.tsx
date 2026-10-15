import React from 'react';

export default function CookiePolicyPage() {
  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-ink mb-6">Cookie Policy</h1>
      <div className="prose max-w-none">
        <p>
          <strong>Effective date:</strong> October 15, 2026
        </p>
        <h2 className="text-xl font-semibold text-ink mt-6">Cookie Policy</h2>
        <p>
          OmniAgent AI does not set any essential or non-essential cookies from the web application itself. All document storage and processing occurs via Cloudflare R2, which does not set browser cookies through the frontend.
        </p>
        <h3 className="text-base font-medium text-ink mt-4">1. Third-Party Cookies</h3>
        <ul className="list-disc list-inside mb-4">
          <li><strong>OpenAI API:</strong> May set session cookies during AI processing. These are managed by OpenAI and are not under our control.</li>
          <li><strong>Hosting provider (Vercel/Render):</strong> May set analytical cookies for server monitoring. These are not accessible via the frontend.</li>
        </ul>

        <h3 className="text-base font-medium text-ink mt-4">2. Browser Controls</h3>
        <p>
          Users can control cookies through their browser settings. Disabling cookies may impact the functionality of the Service.
        </p>

        <h3 className="text-base font-medium text-ink mt-4">3. Consent</h3>
        <p>
          A cookie consent banner will be implemented to manage non-essential tracking. Until implementation, no non-essential cookies are set.
        </p>

        <p>
          <strong>Draft - review by a qualified lawyer before launch.</strong>
        </p>
      </div>
    </div>
  );
}