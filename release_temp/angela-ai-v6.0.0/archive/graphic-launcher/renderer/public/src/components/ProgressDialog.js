import React from 'react';

const ProgressDialog = ({ isOpen, title, message, progress = 0 }) => {
  if (!isOpen) return null;

  return (
    <div className="progress-dialog-overlay">
      <div className="progress-dialog">
        <h3>{title}</h3>
        <p>{message}</p>
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }}></div>
        </div>
        <div className="progress-text">{progress}%</div>
      </div>
    </div>
  );
};

export default ProgressDialog;