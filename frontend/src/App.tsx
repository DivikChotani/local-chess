import { useState, useEffect } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { Chessboard } from "react-chessboard";

function App() {
  const [boardSize, setBoardSize] = useState(
    Math.min(window.innerWidth, window.innerHeight)
  );
  const [gameStarted, setGameStarted] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      setBoardSize(Math.min(window.innerWidth, window.innerHeight));
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);


  return (
    <div 
      className='container'
      >
      { gameStarted ? (
      <Chessboard id="ResponsiveBoard" boardWidth={boardSize * 4/5} /> 
      ):
      (
        <button  
          type="button" 
          onClick={() => setGameStarted(true)}
          className='start-button'
          >
          Start Game
        </button>
      )}
    </div>
  );
}



export default App
