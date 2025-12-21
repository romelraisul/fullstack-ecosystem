import React, { useState } from 'react';

interface SearchResult {
  document_id: string;
  score: number;
  metadata: {
    author: string;
    created_at: string;
    file_type: string;
    tags: string[];
  };
}

const SemanticSearch: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, k: 5 }),
      });
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Semantic Search</h2>
      <div className="flex gap-2 mb-6">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search documents..."
          className="flex-1 p-2 border rounded shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-blue-300"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      <div className="grid gap-4">
        {results.map((result) => (
          <div key={result.document_id} className="p-4 border rounded hover:shadow-md transition-shadow bg-white">
            <div className="flex justify-between items-start">
              <h3 className="text-lg font-semibold text-blue-800">{result.document_id}</h3>
              <span className="text-sm bg-gray-100 px-2 py-1 rounded">Score: {result.score.toFixed(4)}</span>
            </div>
            <div className="mt-2 text-sm text-gray-600">
              <p>Author: {result.metadata.author}</p>
              <p>Date: {new Date(result.metadata.created_at).toLocaleDateString()}</p>
              <div className="flex gap-1 mt-2">
                {result.metadata.tags.map((tag) => (
                  <span key={tag} className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
        {!loading && results.length === 0 && query && (
          <p className="text-center text-gray-500">No results found.</p>
        )}
      </div>
    </div>
  );
};

export default SemanticSearch;
