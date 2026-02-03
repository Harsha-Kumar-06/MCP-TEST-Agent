import Head from 'next/head';
import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>Multi-Agent Marketing Campaign Manager</title>
        <meta name="description" content="AI-powered marketing campaign coordinator" />
      </Head>

      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">
                🤖 Campaign Coordinator
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/campaigns" className="text-gray-700 hover:text-gray-900">
                Campaigns
              </Link>
              <Link href="/campaigns/templates" className="text-gray-700 hover:text-gray-900">
                📚 Templates
              </Link>
              <Link href="/campaigns/create" className="text-gray-700 hover:text-gray-900">
                New Campaign
              </Link>
              <Link href="/contacts" className="text-gray-700 hover:text-gray-900">
                Contacts
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-4xl font-extrabold text-gray-900 sm:text-5xl">
            Multi-Agent Marketing Coordinator
          </h2>
          <p className="mt-4 text-xl text-gray-600">
            AI-powered campaign management with dynamic routing
          </p>
        </div>

        <div className="mt-12 grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          {/* Create Campaign Card */}
          <div className="bg-white overflow-hidden shadow rounded-lg hover:shadow-lg transition-shadow">
            <div className="px-6 py-8">
              <div className="text-4xl mb-4">🎯</div>
              <h3 className="text-lg font-medium text-gray-900">Create Campaign</h3>
              <p className="mt-2 text-sm text-gray-600">
                Design email & SMS campaigns with AI-generated content
              </p>
              <Link 
                href="/campaigns/create"
                className="mt-4 inline-block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              >
                Get Started
              </Link>
            </div>
          </div>

          {/* Upload Contacts Card */}
          <div className="bg-white overflow-hidden shadow rounded-lg hover:shadow-lg transition-shadow">
            <div className="px-6 py-8">
              <div className="text-4xl mb-4">📋</div>
              <h3 className="text-lg font-medium text-gray-900">Upload Contacts</h3>
              <p className="mt-2 text-sm text-gray-600">
                Import contacts from CSV or add them manually
              </p>
              <Link 
                href="/contacts"
                className="mt-4 inline-block bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
              >
                Manage Contacts
              </Link>
            </div>
          </div>

          {/* View Analytics Card */}
          <div className="bg-white overflow-hidden shadow rounded-lg hover:shadow-lg transition-shadow">
            <div className="px-6 py-8">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-lg font-medium text-gray-900">Campaign History</h3>
              <p className="mt-2 text-sm text-gray-600">
                View, manage, and delete past campaigns
              </p>
              <Link 
                href="/campaigns"
                className="mt-4 inline-block bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
              >
                View Campaigns
              </Link>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-16">
          <h3 className="text-2xl font-bold text-gray-900 mb-8">Key Features</h3>
          <div className="grid gap-6 md:grid-cols-2">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <div className="text-2xl">✉️</div>
              </div>
              <div className="ml-4">
                <h4 className="text-lg font-medium text-gray-900">Email Campaigns</h4>
                <p className="mt-1 text-sm text-gray-600">
                  Send via Gmail SMTP with personalization & A/B testing
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0">
                <div className="text-2xl">📱</div>
              </div>
              <div className="ml-4">
                <h4 className="text-lg font-medium text-gray-900">SMS Campaigns</h4>
                <p className="mt-1 text-sm text-gray-600">
                  Powered by Twilio with opt-in management
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0">
                <div className="text-2xl">🤖</div>
              </div>
              <div className="ml-4">
                <h4 className="text-lg font-medium text-gray-900">AI-Powered Coordination</h4>
                <p className="mt-1 text-sm text-gray-600">
                  Intelligent routing to specialized agents
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0">
                <div className="text-2xl">⚖️</div>
              </div>
              <div className="ml-4">
                <h4 className="text-lg font-medium text-gray-900">Compliance Checking</h4>
                <p className="mt-1 text-sm text-gray-600">
                  CAN-SPAM, TCPA, and GDPR compliance verification
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>

      <style jsx global>{`
        html, body {
          padding: 0;
          margin: 0;
          font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Oxygen,
            Ubuntu, Cantarell, Fira Sans, Droid Sans, Helvetica Neue, sans-serif;
        }
        * {
          box-sizing: border-box;
        }
      `}</style>
    </div>
  );
}
