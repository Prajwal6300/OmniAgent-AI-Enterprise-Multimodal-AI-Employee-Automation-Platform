import React from 'react';

export default function TermsOfServicePage() {
  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-ink mb-6">Terms of Service</h1>
      <div className="prose max-w-none">
        <p>
          <strong>Effective date:</strong> October 15, 2026
        </p>
        <p>
          These Terms of Service govern your use of the OmniAgent AI platform. By accessing or using the Service, you accept these Terms. If you disagree with any part of the Terms, you may not access the Service.
        </p>

        <h2 className="text-xl font-semibold text-ink mt-8">1. Acceptance of Terms</h2>
        <p>
          By using the Service, you represent that you are at least 18 years of age. The Service is not intended for anyone under the age of 18.
        </p>

        <h2 className="text-xl font-semibold text-ink mt-8">2. Account Responsibility</h2>
        <ol className="list-decimal list-inside mb-4">
          <li>You are responsible for maintaining the security of your account and password.</li>
          <li>You are responsible for all activities that occur under your account.</li>
          <li>You must notify us immediately of any unauthorized use of your account.</li>
          <li>You are responsible for the content you post on or through the Service.</li>
        </ol>

        <h2 className="text-xl font-semibold text-ink mt-8">3. AI Output Disclaimer</h2>
        <p>
          The Service uses artificial intelligence to generate content, insights, and recommendations. We do not make any guarantees or warranties of any kind, express or implied, regarding the accuracy, reliability, or completeness of AI output. AI output should be independently verified before use. Use of AI output is at your own risk.
        </p>

        <h2 className="text-xl font-semibold text-ink mt-8">4. Intellectual Property</h2>
        <p>
          Our Service and its original content, features and functionality are owned and are protected by international intellectual property laws. The Service is not licensed to you, and we retain all ownership rights.
        </p>

        <h2 className="text-xl font-semibold text-ink mt-8">5. Limitation of Liability</h2>
        <p>
          To the maximum extent permitted by law, including without limitation U.S. law limitation of liability, in no event shall OmniAgent AI, its directors, employees, partners, agents, suppliers, or affiliates be liable for any indirect, consequential, incidental, special, punitive, or exemplary damages, including without limitation loss of profits, goodwill, data, or other intangible losses, resulting from:
        </p>
        <ul className="list-disc list-inside mb-4">
          <li>Access to or use of or inability to access or use the Service.</li>
          <li>any conduct or content of any third party on the Service.</li>
          <li>any content obtained from the Service.</li>
          <li>relevant transactions made in relation to the Service.</li>
        </ul>
        <p>
          Some jurisdictions do not allow the exclusion of certain warranties or the limitation or liability, so some or all of the above exclusions and limitations may not apply to you. In those jurisdictions, our liability shall be limited to the maximum extent permitted by the applicable law.
        </p>

        <h2 className="text-xl font-semibold text-ink mt-8">6. Termination</h2>
        <p>
          We may terminate or suspend your account immediately, without prior notice or liability, for any reason whatsoever, including without limitation breach of these Terms.
        </p>

        <h2 className="text-xl font-semibold text-ink mt-8">7. Governing Law</h2>
        <p>
          These Terms shall be governed by and construed in accordance with the laws of the jurisdiction specified in the company records, without regard to its conflict of law principles. Certain provisions of these Terms may be governed by other applicable laws. If any provision of these Terms is determined to be invalid or unenforceable pursuant to applicable law, the remaining provisions will remain in effect.
        </p>
        <p>
          <strong>Draft - review by a qualified lawyer before launch.</strong>
        </p>
      </div>
    </div>
  );
}