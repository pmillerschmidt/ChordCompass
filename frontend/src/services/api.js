const API_URL = 'http://localhost:8000';

export const generateProgression = async (seed, length) => {
  try {
    const response = await fetch(`${API_URL}/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ seed, length }),
    });

    // Add better error handling
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Server error');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};