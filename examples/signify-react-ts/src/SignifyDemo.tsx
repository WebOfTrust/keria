import { useState, useEffect } from 'react';

export function SignifyDemo(args:{ text:string, onClick:any }) {
  const [response, setResponse] = useState('');
  const text = args.text;
  const onClick = args.onClick;

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
