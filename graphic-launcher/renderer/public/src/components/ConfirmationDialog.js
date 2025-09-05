import React from 'react';

const ConfirmationDialog = ({ isOpen, title, message, onConfirm, onCancel }) => {
  if (!isOpen) return null;

  return (
    <div className="confirmation-dialog-overlay">
      <div className="confirmation-dialog">
        <h3>{title}</h3>
        <p>{message}</p>
        <div className="dialog-buttons">
          <button className="confirm-button" onClick={onConfirm}>確認</button>
          <button className="cancel-button" onClick={onCancel}>取消</button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmationDialog;