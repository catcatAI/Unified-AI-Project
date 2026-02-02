import React, { useState } from 'react';
import { searchQuery } from '../api/chat';

const Search: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const response = await searchQuery(query);
      setResults(response);
    } catch (error) {
      console.error('Search failed:', error);
      setResults({ error: 'Search failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="search-page">
      <h2>智能搜索</h2>
      
      <div className="search-section">
        <div className="search-input-container">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入搜索查询..."
            className="search-input"
          />
          <button 
            onClick={handleSearch} 
            disabled={loading || !query.trim()}
            className="search-button"
          >
            {loading ? '搜索中...' : '搜索'}
          </button>
        </div>
      </div>

      {results && (
        <div className="results-section">
          {results.error ? (
            <div className="error">错误: {results.error}</div>
          ) : (
            <div className="search-results">
              <h3>搜索结果 ({results.total || 0})</h3>
              {results.results && results.results.map((result: any, index: number) => (
                <div key={index} className="result-item">
                  <h4>{result.title}</h4>
                  <p>{result.snippet}</p>
                  {result.url && (
                    <a href={result.url} target="_blank" rel="noopener noreferrer">
                      {result.url}
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Search;