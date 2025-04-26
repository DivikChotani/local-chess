import { useState, useEffect } from 'react'
import './App.css'
import { Chessboard } from "react-chessboard";
import axios from 'axios';

function App() {
  const [boardSize, setBoardSize] = useState(
    Math.min(window.innerWidth, window.innerHeight)
  );
  const [gameStarted, setGameStarted] = useState(false);
  const [fen, setFen] = useState("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

  useEffect(() => {
    const handleResize = () => {
      setBoardSize(Math.min(window.innerWidth, window.innerHeight));
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  function startGame(){
    setGameStarted(true)
    let config = {
      method: 'get',
      maxBodyLength: Infinity,
      url: 'http://127.0.0.1:5000/initialize-board',
      headers: { }
    };
    
    axios.request(config)
    .then((response) => {
      let t:string = (response.data.fen);
      console.log(typeof(t))
      setFen(t)
    })
    .catch((error) => {
      console.log(error);
    });

  }


  return (
    <div 
      className='container'
      >
      { gameStarted ? (
      <Chessboard 
        id="ResponsiveBoard" 
        boardWidth={boardSize * 4/5}
        position={fen} 
        /> 
      ):
      (
        <button  
          type="button" 
          onClick={() => startGame()}
          className='start-button'
          >
          Start Game
        </button>
      )}
    </div>
  );
}



export default App
