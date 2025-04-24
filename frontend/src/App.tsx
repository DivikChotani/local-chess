import { useState, useEffect } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { Chessboard } from "react-chessboard";

function App() {
  const [boardSize, setBoardSize] = useState(
    Math.min(window.innerWidth, window.innerHeight)
  );

  useEffect(() => {
    const handleResize = () => {
      setBoardSize(Math.min(window.innerWidth, window.innerHeight));
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '90vh' }}>
      <Chessboard id="ResponsiveBoard" boardWidth={boardSize * 4/5} />
    </div>
  );
}



export default App
