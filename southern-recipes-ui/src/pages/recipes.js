import { useState } from 'react';

export default function Recipes() {
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('idle'); // idle | loading | error | done
  const [source, setSource] = useState(null);
  const [recipes, setRecipes] = useState([]);
  const [errorMsg, setErrorMsg] = useState('');

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

  const handleSearch = async () => {
    if (!query.trim()) return;
    setStatus('loading');
    setErrorMsg('');
    try {
      const res = await fetch(
        `${API_BASE}/api/recipe?q=${encodeURIComponent(query)}`
      );
      const data = await res.json();
      if (data.source === 'local') {
        setSource('Local Matches');
        setRecipes(data.recipes);
      } else if (data.source === 'ai') {
        setSource('AI Generated');
        setRecipes([data.recipe]);
      } else {
        throw new Error(data.message || 'Unknown error');
      }
      setStatus('done');
    } catch (err) {
      setErrorMsg(err.message || 'Fetch failed');
      setStatus('error');
    }
  };

  return (
    <div style={{ maxWidth: '600px', margin: '2rem auto', fontFamily: 'sans-serif' }}>
      <h1 style={{ fontSize: '1.5rem', fontFamily: 'serif', color: '#2F4F4F' }}>
        Recipe Finder
      </h1>
      <div style={{ display: 'flex', gap: '0.5rem', margin: '1rem 0' }}>
        <input
          type="text"
          placeholder="Enter dish or ingredients"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{
            flex: 1,
            padding: '0.5rem',
            fontSize: '1rem',
            borderRadius: '4px',
            border: '1px solid #ccc'
          }}
        />
        <button
          onClick={handleSearch}
          disabled={status === 'loading'}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#C75B12',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          {status === 'loading' ? 'Searching…' : 'Search'}
        </button>
      </div>
      {status === 'error' && <p style={{ color: 'red' }}>Error: {errorMsg}</p>}
      {status === 'done' && (
        <div>
          <h2 style={{ fontSize: '1.25rem', fontFamily: 'serif', color: '#3F5D3D' }}>
            {source}
          </h2>
          {recipes.map((r, idx) => (
            <div
              key={idx}
              style={{
                border: '1px solid #ccc',
                borderRadius: '6px',
                padding: '1rem',
                marginBottom: '1rem',
                backgroundColor: '#fff',
                boxShadow: '0 2px 6px rgba(0,0,0,0.1)'
              }}
            >
              <h3 style={{ margin: 0, fontFamily: 'serif', color: '#3F5D3D' }}>
                {r.title}
              </h3>
              <div style={{ marginTop: '0.5rem' }}>
                <strong>Ingredients:</strong>
                <ul>
                  {r.ingredients.map((ing, i) => (
                    <li key={i}>{ing}</li>
                  ))}
                </ul>
              </div>
              <div style={{ marginTop: '0.5rem' }}>
                <strong>Steps:</strong>
                <ol>
                  {r.steps.map((step, i) => (
                    <li key={i}>{step}</li>
                  ))}
                </ol>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
