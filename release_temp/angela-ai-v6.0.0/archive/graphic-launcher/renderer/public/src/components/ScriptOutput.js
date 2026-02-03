import React, { useState, useEffect } from 'react';

const ScriptOutput = ({ initialOutput = '' }) => {
  const [output, setOutput] = useState(initialOutput);
  const [isAutoScroll, setIsAutoScroll] = useState(true);

  // Create a ref for the output container
  const outputRef = React.useRef(null);

  // Auto-scroll to bottom when output changes
  useEffect(() => {
    if (isAutoScroll && outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output, isAutoScroll]);

  // Handle scroll events to toggle auto-scroll
  const handleScroll = (e) => {
    const { scrollTop, scrollHeight, clientHeight } = e.target;
    const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10;
    setIsAutoScroll(isAtBottom);
  };

  // Clear output
  const clearOutput = () => {
    setOutput('');
  };

  return (
    <div className="script-output">
      <div className="output-header">
        <h3>輸出結果</h3>
        <div className="output-controls">
          <button onClick={clearOutput}>清除</button>
          <label>
            <input
              type="checkbox"
              checked={isAutoScroll}
              onChange={(e) => setIsAutoScroll(e.target.checked)}
            />
            自動滾動
          </label>
        </div>
      </div>
      <div
        className="output-content"
        ref={outputRef}
        onScroll={handleScroll}
      >
        <pre>{output}</pre>
      </div>
    </div>
  );
};

export default ScriptOutput;