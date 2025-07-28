import React from "react";

const Game = () => {
  const startGame = () => {
    // This would need to call the Electron main process to launch the game.
    // The IPC logic would be set up in preload.js and main.js.
    if (window.electronAPI) {
      window.electronAPI.invoke("game:start");
    }
  };

  return (
    <div>
      <h1>Game</h1>
      <p>This is the game interface.</p>
      <button onClick={startGame}>Start Game</button>
    </div>
  );
};

export default Game;
