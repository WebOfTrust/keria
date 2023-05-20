import { useState, useEffect, useRef } from 'react';

export function SignifyDemo({ text, onClick }) {
  const [response, setResponse] = useState('');

  useEffect(() => {
    // Additional initialization or setup code can be added here
  }, []);

  const handleClick = async () => {
    try {
      const result = await onClick();
      setResponse(result);
    } catch (error) {
      console.log(error);
      setResponse('Error executing function');
    }
  };

  const inputRef = useRef(null);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.width = 'auto';
      inputRef.current.style.width = `${inputRef.current.scrollWidth}px`;
    }
  }, []);

  return (
    <div className="card">
      <button onClick={handleClick} className="button">
        {text}
      </button>
      <div
        style={{
          whiteSpace: 'pre-wrap',
          wordWrap: 'break-word',
          width: '100%',
          height: 'auto',
          textAlign: 'left',
          padding: '1rem',
          backgroundColor: '#eee',
          borderRadius: '0.5rem',
          marginTop: '1rem',
          border: '1px solid black',
        }}
      >
        Status: {response}
      </div>
    </div>
  );
}
