module.exports = {
  ci: {
    collect: {
      startServerCommand: 'npm start',
      url: ['http://localhost:3001/', 'http://localhost:3001/pricing', 'http://localhost:3001/auth/signup'],
      numberOfRuns: 3,
      settings: {
        chromeFlags: '--no-sandbox --headless --disable-gpu',
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
    assert: {
      preset: 'lighthouse:recommended',
      assertions: {
        'categories:performance': ['warn', { minScore: 0.9 }],
        'categories:accessibility': ['error', { minScore: 0.95 }],
        'categories:seo': ['error', { minScore: 0.9 }],
      },
    },
  },
};
